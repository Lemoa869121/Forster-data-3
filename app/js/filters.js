// Filtres d'interface -> SQL paramétré.
// Chaque filtre actif ajoute une condition sur le PV principal (pv), en tenant compte de ses extensions
// et reconductions via la table temporaire `rat` (copie indexée de v_document_rattachement, créée au chargement).
// Les facettes (compteurs par option) réutilisent les mêmes conditions en excluant la facette elle-même.
export const normRef = s => (s || '').replace(/[\s.]/g, '').toUpperCase();
export const normTxt = s => (s || '').normalize('NFKD').replace(/[̀-ͯ]/g, '').toLowerCase();

export const PREPARATION = `
  CREATE TEMP TABLE IF NOT EXISTS rat AS SELECT document_id, pv_principal_id FROM v_document_rattachement;
  CREATE INDEX IF NOT EXISTS temp.ix_rat ON rat(pv_principal_id, document_id);
  CREATE INDEX IF NOT EXISTS temp.ix_rat2 ON rat(document_id);
  CREATE TEMP TABLE IF NOT EXISTS cls AS SELECT document_id, classe_normalisee, duree_min, critere_i, critere_w, statut_extraction FROM v_classement_feu;
  CREATE INDEX IF NOT EXISTS temp.ix_cls ON cls(document_id);
  CREATE TEMP TABLE IF NOT EXISTS pa AS
    SELECT DISTINCT CASE WHEN v.systeme_id LIKE 'SYS-FUEGO-LIGHT%' THEN 'SYS-FUEGO-LIGHT' ELSE v.systeme_id END AS sysgrp,
      CASE WHEN v.typologie_code IN ('chassis_fixe','cloison_vitree','cloison_vitree_bord_a_bord') THEN 'fixe' ELSE v.typologie_code END AS famille,
      CASE v.domaine_code
        WHEN 'effraction' THEN 'RC' || substr(e.classe_rc, 3, 1)
        WHEN 'balistique' THEN CASE WHEN b.classe LIKE 'FB%' THEN b.classe END
        WHEN 'explosion' THEN x.classe
        WHEN 'aev' THEN 'AEV'
        WHEN 'issue_secours' THEN 'ANTIPANIQUE' END AS code,
      v.domaine_code, v.document_id, v.classe_normalisee
    FROM v_performance_multi v
    LEFT JOIN perf_effraction e ON e.performance_id = v.performance_id
    LEFT JOIN perf_balistique b ON b.performance_id = v.performance_id
    LEFT JOIN perf_explosion x ON x.performance_id = v.performance_id
   WHERE v.domaine_code NOT IN ('feu') AND v.systeme_id IS NOT NULL AND v.systeme_id <> 'SYS-PRESTO' AND v.typologie_code IS NOT NULL
  UNION
    SELECT DISTINCT CASE WHEN v.systeme_id LIKE 'SYS-FUEGO-LIGHT%' THEN 'SYS-FUEGO-LIGHT' ELSE v.systeme_id END,
      CASE WHEN v.typologie_code IN ('chassis_fixe','cloison_vitree','cloison_vitree_bord_a_bord') THEN 'fixe' ELSE v.typologie_code END,
      'RW' || t.seuil, 'acoustique', v.document_id, v.classe_normalisee
    FROM v_performance_multi v JOIN perf_acoustique a ON a.performance_id = v.performance_id
    JOIN (SELECT 35 AS seuil UNION SELECT 40 UNION SELECT 45) t ON a.rw_db >= t.seuil
   WHERE v.systeme_id IS NOT NULL AND v.systeme_id <> 'SYS-PRESTO' AND v.typologie_code IS NOT NULL;
  CREATE INDEX IF NOT EXISTS temp.ix_pa ON pa(sysgrp, famille, code);
  CREATE TEMP TABLE IF NOT EXISTS cfg AS
    SELECT r.pv_principal_id, CASE WHEN c.systeme_id LIKE 'SYS-FUEGO-LIGHT%' THEN 'SYS-FUEGO-LIGHT' ELSE c.systeme_id END AS sysgrp,
      CASE WHEN c.typologie_code IN ('chassis_fixe','cloison_vitree','cloison_vitree_bord_a_bord') THEN 'fixe' ELSE c.typologie_code END AS famille
    FROM rat r JOIN configuration c ON c.document_id = r.document_id WHERE c.systeme_id IS NOT NULL GROUP BY 1,2,3;
  CREATE INDEX IF NOT EXISTS temp.ix_cfg ON cfg(pv_principal_id);`;

// Options « performance complémentaire » (rapports d'essais du même système, même famille de typologie)
export const COMPLEMENTS = { RC2: 'RC2', RC3: 'RC3', RC4: 'RC4', FB4: 'FB4', FB5: 'FB5', FB6: 'FB6', FB7: 'FB7', EPR1: 'EPR1',
  RW35: 'Rw ≥ 35 dB', RW40: 'Rw ≥ 40 dB', RW45: 'Rw ≥ 45 dB', AEV: 'AEV', ANTIPANIQUE: 'EN 179 / EN 1125' };
export const TYPES_RAPPORT = ['rapport_essai', 'rapport_classement', 'avis_expertise', 'certificat', 'synthese_fabricant', 'passeport_ce', 'fiche_technique'];

const VAL = `COALESCE(ve.date_validite_effective, pv.date_validite)`;
const BASE = `FROM document pv LEFT JOIN v_validite_effective ve ON ve.document_id = pv.id LEFT JOIN fichier_source fs ON fs.id = pv.fichier_source_id`;
const DANS_PV = t => `EXISTS (SELECT 1 FROM rat r2 ${t} WHERE r2.pv_principal_id = pv.id AND `;

export const LIBELLES_VERRIER = { VETR: 'Vetrotech Saint-Gobain', PILK: 'Pilkington', PYRO: 'Pyroguard', POLF: 'Polflam', AGC: 'AGC', GTRO: 'Glas Trösch' };
const OBJETS_DIM = {
  passage: ['passage_libre'], vantail: ['vantail_hors_tout', 'vantail_principal', 'vantail_secondaire'],
  vitrage: ['vitrage_hors_tout', 'vitrage_clair'], ouvrage: ['cloison', 'facade_entre_dalles', 'ensemble', 'facade'],
};

const FD_LIENS = `FROM rat r2 JOIN fiche_forsterdata fa ON fa.document_pv_id = r2.document_id
      JOIN lien_forsterdata l ON fa.id IN (l.fiche_a, l.fiche_b)
      JOIN fiche_forsterdata fb ON fb.id = CASE WHEN l.fiche_a = fa.id THEN l.fiche_b ELSE l.fiche_a END
      WHERE r2.pv_principal_id = pv.id AND fb.categorie IN ('rc','fb')`;
const liste = (nom, valeurs, params) => valeurs.map((v, i) => { params[`:${nom}${i}`] = v; return `:${nom}${i}`; }).join(',');
const iso = d => d.toISOString().slice(0, 10);

// Chaque filtre : (state, params) => condition SQL ou null
const FILTRES = {
  reference: (s, p) => s.reference ? (p[':reference'] = normRef(s.reference),
    `${DANS_PV('JOIN document_composant dc ON dc.document_id = r2.document_id LEFT JOIN reference_composant rc ON rc.id = dc.reference_id')}
      (rc.reference_normalisee LIKE '%' || :reference || '%'
       OR dc.reference_id IN (SELECT reference_id FROM reference_alias WHERE upper(replace(replace(alias,' ',''),'.','')) LIKE '%' || :reference || '%')))`) : null,
  texte: (s, p) => s.texte ? (p[':texte'] = normTxt(s.texte),
    `${DANS_PV('JOIN recherche_index ri ON ri.document_id = r2.document_id')} ri.texte LIKE '%' || :texte || '%')`) : null,
  systeme: (s, p) => s.systeme.length ? `${DANS_PV('JOIN document_systeme ds ON ds.document_id = r2.document_id')} ds.systeme_id IN (${liste('sys', s.systeme, p)}))` : null,
  typologie: (s, p) => s.typologie.length ? `${DANS_PV('JOIN configuration c ON c.document_id = r2.document_id')} c.typologie_code IN (${liste('typo', s.typologie, p)}))` : null,
  vantaux: s => s.vantaux === '1'
    ? `(${DANS_PV('JOIN configuration c ON c.document_id = r2.document_id')} c.nb_vantaux_min = 1)
        OR lower(pv.objet) LIKE '%un vantail%' OR lower(pv.objet) LIKE '%un ou deux vantaux%' OR lower(pv.objet) LIKE '%1 vantail%'
        OR lower(pv.objet) LIKE '%1 ou 2 vantaux%' OR lower(pv.objet) LIKE '%1 et 2 vantaux%' OR lower(pv.objet) LIKE '%un et deux vantaux%')`
    : s.vantaux === '2'
    ? `(${DANS_PV('JOIN configuration c ON c.document_id = r2.document_id')} c.nb_vantaux_max = 2)
        OR lower(pv.objet) LIKE '%deux vantaux%' OR lower(pv.objet) LIKE '%2 vantaux%')` : null,
  verrier: (s, p) => s.verrier.length ? `fs.code_fournisseur_vitrage IN (${liste('verr', s.verrier, p)})` : null,
  performance: (s, p) => {
    if (!s.critere && !s.duree && !s.classe_lue) return null;
    p[':duree'] = Number(s.duree || 0); p[':lue'] = s.classe_lue ? 1 : 0;
    const crit = s.critere === 'EI' ? 'AND f.critere_i = 1' : s.critere === 'EW' ? 'AND f.critere_w = 1' : '';
    return `${DANS_PV('JOIN cls f ON f.document_id = r2.document_id')} f.duree_min >= :duree ${crit} AND (:lue = 0 OR f.statut_extraction <> 'non_trouve'))`;
  },
  vitrage: (s, p) => {
    if (!s.gamme && !s.type_vitrage.length) return null;
    const c = [];
    if (s.gamme) { p[':gamme'] = s.gamme; c.push('v.gamme = :gamme'); }
    if (s.type_vitrage.length) c.push(`v.type_vitrage_code IN (${liste('tv', s.type_vitrage, p)})`);
    return `${DANS_PV('JOIN document_composant dc ON dc.document_id = r2.document_id JOIN dc_vitrage v ON v.document_composant_id = dc.id')} ${c.join(' AND ')})`;
  },
  categorie: (s, p) => s.categorie ? (p[':categorie'] = s.categorie,
    `${DANS_PV('JOIN document_composant dc ON dc.document_id = r2.document_id')} dc.categorie_code = :categorie)`) : null,
  fonction: (s, p) => s.fonction ? (p[':fonction'] = s.fonction,
    `${DANS_PV('JOIN document_composant dc ON dc.document_id = r2.document_id JOIN dc_serrure se ON se.document_composant_id = dc.id')} se.fonction_code = :fonction)`) : null,
  antipanique: s => s.antipanique ? `${DANS_PV('JOIN document_composant dc ON dc.document_id = r2.document_id LEFT JOIN dc_serrure se ON se.document_composant_id = dc.id')}
      (se.antipanique = 1 OR dc.categorie_code = 'barre_antipanique' OR lower(dc.designation_document) LIKE '%anti%panique%'))` : null,
  dimensions: (s, p) => {
    if (!s.largeur && !s.hauteur) return null;
    const objs = OBJETS_DIM[s.objet_dim || 'passage'];
    const cond = g => `EXISTS (SELECT 1 FROM dimension dm WHERE dm.format_id = df.id AND dm.grandeur_code = '${g}' AND dm.nature_code = 'autorise_max' AND (dm.sans_limite = 1 OR dm.valeur_norm >= :${g}))`;
    const c = [];
    if (s.largeur) { p[':largeur'] = Number(s.largeur); c.push(cond('largeur')); }
    if (s.hauteur) { p[':hauteur'] = Number(s.hauteur); c.push(cond('hauteur')); }
    const ins = liste('obj', objs, p);
    const ok = `${DANS_PV('JOIN dimension_format df ON df.document_id = r2.document_id')} df.objet_code IN (${ins}) AND ${c.join(' AND ')})`;
    // option : garder les PV pour lesquels aucune dimension de ce type n'a été extraite (inconnu ≠ non conforme)
    return s.dim_inconnue ? `(${ok} OR NOT ${DANS_PV('JOIN dimension_format df ON df.document_id = r2.document_id')} df.objet_code IN (${ins})))` : ok;
  },
  support: (s, p) => (s.support.length || s.allege) ? `${DANS_PV('JOIN support_pose sp ON sp.document_id = r2.document_id')}
      ${s.support.length ? `sp.type_support_code IN (${liste('sup', s.support, p)})` : '1'} ${s.allege ? 'AND sp.allege_autorisee = 1' : ''})` : null,
  etat: (s, p) => {
    const t = new Date(); p[':aujourdhui'] = iso(t);
    if (s.etat === 'valide') return `${VAL} >= :aujourdhui`;
    if (s.etat === 'echu') return `${VAL} < :aujourdhui`;
    if (s.etat === 'bientot') { const a = new Date(t); a.setFullYear(a.getFullYear() + 1); p[':dans1an'] = iso(a); return `${VAL} BETWEEN :aujourdhui AND :dans1an`; }
    return null;
  },
  valide: (s, p) => s.valide ? (p[':valide'] = s.valide, `${VAL} >= :valide`) : null,
  verifie: s => s.verifie ? `pv.fichier_source_id NOT LIKE 'FIC-AUTO%' AND pv.id NOT LIKE 'DOC-RAP-%'` : null,
  complement: (s, p) => s.complement.length
    ? `EXISTS (SELECT 1 FROM cfg JOIN pa ON pa.sysgrp = cfg.sysgrp AND pa.famille = cfg.famille WHERE cfg.pv_principal_id = pv.id AND pa.code IN (${liste('cpl', s.complement, p)}))` : null,
  domaine: (s, p) => s.domaine.length ? `pv.domaine_code IN (${liste('dom', s.domaine, p)})` : null,
  cumul_fd: (s, p) => s.cumul_fd.length ? `EXISTS (SELECT 1 ${FD_LIENS} AND fb.classe IN (${liste('cfd', s.cumul_fd, p)}))` : null,
  cumul: s => s.cumul ? `EXISTS (SELECT 1 FROM cfg JOIN cumul_performance cp ON (CASE WHEN cp.systeme_id LIKE 'SYS-FUEGO-LIGHT%' THEN 'SYS-FUEGO-LIGHT' ELSE cp.systeme_id END) = cfg.sysgrp
      AND (CASE WHEN cp.typologie_code IN ('chassis_fixe','cloison_vitree','cloison_vitree_bord_a_bord') THEN 'fixe' ELSE cp.typologie_code END) = cfg.famille
      WHERE cfg.pv_principal_id = pv.id AND 'feu' IN (cp.domaine_a, cp.domaine_b))` : null,
};
// Filtres sans objet pour les rapports d'essais (pas de validité, pas de classement feu au sens PV)
const SANS_OBJET_RAPPORTS = ['etat', 'valide', 'performance', 'verrier', 'complement', 'cumul', 'vantaux', 'cumul_fd'];

// Facette -> nom du filtre qu'elle ne doit pas s'appliquer à elle-même
const EXCLUSION = { systeme: 'systeme', typologie: 'typologie', verrier: 'verrier', support: 'support', gamme: 'vitrage', categorie: 'categorie',
  complement: 'complement', domaine: 'domaine', cumul_fd: 'cumul_fd' };

export const estRapports = s => s.type_doc === 'rapports';

export function where(state, exclure = null) {
  const params = {};
  const w = [`pv.present_dans_corpus = 1`];
  if (estRapports(state)) w.push(`pv.id LIKE 'DOC-RAP-%'`);
  else { w.push(`pv.type_code = :type_doc`); params[':type_doc'] = state.type_doc || 'pv_classement'; }
  for (const [k, f] of Object.entries(FILTRES)) {
    if (k === exclure) continue;
    if (estRapports(state) ? SANS_OBJET_RAPPORTS.includes(k) : k === 'domaine') continue;
    const c = f(state, params);
    if (c) w.push(c);
  }
  return { sql: w.join('\n  AND '), params };
}

const TRI = {
  numero: 'pv.numero_normalise', validite_desc: `${VAL} DESC`, validite_asc: `${VAL} ASC`, emission_desc: 'pv.date_emission DESC',
};

export function buildQuery(state, tri = 'numero') {
  const { sql: w, params } = where(state);
  const sql = `SELECT pv.id, pv.numero_normalise, pv.objet, (pv.fichier_source_id LIKE 'FIC-AUTO%') AS auto,
      ${VAL} AS validite, ve.derniere_reconduction, pv.date_emission, fs.code_fournisseur_vitrage AS verrier, fs.nom_fichier,
      (SELECT group_concat(DISTINCT s.nom) FROM document_systeme ds JOIN systeme s ON s.id = ds.systeme_id WHERE ds.document_id = pv.id) AS systemes,
      (SELECT group_concat(DISTINCT f.classe_normalisee || CASE WHEN f.statut_extraction = 'non_trouve' THEN '*' ELSE '' END)
         FROM rat r2 JOIN cls f ON f.document_id = r2.document_id WHERE r2.pv_principal_id = pv.id) AS classements,
      pv.domaine_code AS domaine, pv.type_code,
      (SELECT group_concat(DISTINCT p.classe_normalisee) FROM performance p WHERE p.document_id = pv.id AND p.domaine_code <> 'feu') AS autres_perfs,
      (SELECT group_concat(DISTINCT pa.code) FROM cfg JOIN pa ON pa.sysgrp = cfg.sysgrp AND pa.famille = cfg.famille WHERE cfg.pv_principal_id = pv.id AND pa.code IS NOT NULL) AS complements,
      (SELECT count(*) FROM cumul_performance cp WHERE cp.document_id = pv.id) AS nb_cumuls_enonces,
      (SELECT group_concat(DISTINCT fb.classe) ${FD_LIENS}) AS cumul_fd,
      (SELECT group_concat(DISTINCT t.libelle) FROM rat r3 JOIN configuration c ON c.document_id = r3.document_id JOIN ref_typologie t ON t.code = c.typologie_code WHERE r3.pv_principal_id = pv.id) AS typologies,
      (SELECT count(*) FROM document_relation dr WHERE dr.document_cible_id = pv.id AND dr.type_relation_code = 'etend') AS nb_extensions,
      (SELECT count(*) FROM controle_humain ch JOIN rat r2 ON r2.document_id = ch.document_id WHERE r2.pv_principal_id = pv.id AND ch.statut = 'ouvert') AS nb_controles
    ${BASE}
    WHERE ${w}
    ORDER BY ${TRI[tri] || TRI.numero}`;
  return { sql, params };
}

// Occurrences de la référence recherchée dans un PV (pour expliquer le résultat)
export function dimInconnueQuery(pvId, objet) {
  const p = { ':pv': pvId }; const ins = liste('o', OBJETS_DIM[objet || 'passage'], p);
  return { sql: `SELECT count(*) AS n FROM rat r2 JOIN dimension_format df ON df.document_id = r2.document_id WHERE r2.pv_principal_id = :pv AND df.objet_code IN (${ins})`, params: p };
}

export function hitsQuery(pvId, ref) {
  return {
    sql: `SELECT d.numero_normalise AS doc, dc.reference_brute AS ref, dc.categorie_code AS cat, sp.page_doc AS page, sp.planche
          FROM rat r2 JOIN document_composant dc ON dc.document_id = r2.document_id JOIN document d ON d.id = dc.document_id
          LEFT JOIN reference_composant rc ON rc.id = dc.reference_id LEFT JOIN source_page sp ON sp.id = dc.source_page_id
          WHERE r2.pv_principal_id = :pv AND rc.reference_normalisee LIKE '%' || :ref || '%' LIMIT 6`,
    params: { ':pv': pvId, ':ref': normRef(ref) },
  };
}

// Requêtes de facettes : compte des PV par option, filtres courants appliqués sauf la facette elle-même
export function facetQuery(nom, state) {
  const { sql: w, params } = where(state, EXCLUSION[nom]);
  const sub = `SELECT pv.id ${BASE} WHERE ${w}`;
  const q = {
    systeme: `SELECT s.id AS code, s.nom AS libelle, count(DISTINCT r.pv_principal_id) AS n FROM rat r JOIN document_systeme ds ON ds.document_id = r.document_id
              JOIN systeme s ON s.id = ds.systeme_id WHERE r.pv_principal_id IN (${sub}) GROUP BY 1 ORDER BY s.nom`,
    typologie: `SELECT t.code, t.libelle, count(DISTINCT r.pv_principal_id) AS n FROM rat r JOIN configuration c ON c.document_id = r.document_id
              JOIN ref_typologie t ON t.code = c.typologie_code WHERE r.pv_principal_id IN (${sub}) GROUP BY 1 ORDER BY t.libelle`,
    verrier: `SELECT fs.code_fournisseur_vitrage AS code, fs.code_fournisseur_vitrage AS libelle, count(*) AS n ${BASE}
              WHERE pv.id IN (${sub}) AND fs.code_fournisseur_vitrage IS NOT NULL GROUP BY 1 ORDER BY 1`,
    support: `SELECT t.code, t.libelle, count(DISTINCT r.pv_principal_id) AS n FROM rat r JOIN support_pose sp ON sp.document_id = r.document_id
              JOIN ref_type_support t ON t.code = sp.type_support_code WHERE r.pv_principal_id IN (${sub}) GROUP BY 1 ORDER BY t.famille DESC, t.libelle`,
    gamme: `SELECT v.gamme AS code, v.gamme AS libelle, count(DISTINCT r.pv_principal_id) AS n FROM rat r JOIN document_composant dc ON dc.document_id = r.document_id
              JOIN dc_vitrage v ON v.document_composant_id = dc.id WHERE r.pv_principal_id IN (${sub}) GROUP BY 1 ORDER BY 1`,
    categorie: `SELECT c.code, c.libelle, count(DISTINCT r.pv_principal_id) AS n FROM rat r JOIN document_composant dc ON dc.document_id = r.document_id
              JOIN ref_categorie_composant c ON c.code = dc.categorie_code WHERE r.pv_principal_id IN (${sub}) GROUP BY 1 ORDER BY c.libelle`,
    complement: `SELECT pa.code, pa.code AS libelle, count(DISTINCT cfg.pv_principal_id) AS n FROM cfg JOIN pa ON pa.sysgrp = cfg.sysgrp AND pa.famille = cfg.famille
              WHERE cfg.pv_principal_id IN (${sub}) AND pa.code IS NOT NULL GROUP BY 1`,
    cumul_fd: `SELECT fb.classe AS code, fb.classe AS libelle, count(DISTINCT pv.id) AS n FROM document pv JOIN rat r2 ON r2.pv_principal_id = pv.id
              JOIN fiche_forsterdata fa ON fa.document_pv_id = r2.document_id JOIN lien_forsterdata l ON fa.id IN (l.fiche_a, l.fiche_b)
              JOIN fiche_forsterdata fb ON fb.id = CASE WHEN l.fiche_a = fa.id THEN l.fiche_b ELSE l.fiche_a END
              WHERE fb.categorie IN ('rc','fb') AND pv.id IN (${sub}) GROUP BY 1 ORDER BY fb.categorie DESC, 1`,
    domaine: `SELECT d.code, d.libelle, count(pv.id) AS n FROM ref_domaine_performance d LEFT JOIN document pv ON pv.domaine_code = d.code AND pv.id IN (${sub})
              GROUP BY 1 HAVING d.code <> 'feu' OR n > 0 ORDER BY d.libelle`,
  }[nom];
  return { sql: q, params };
}
export const FACETTES = ['systeme', 'typologie', 'verrier', 'support', 'gamme', 'categorie', 'complement', 'domaine', 'cumul_fd'];
