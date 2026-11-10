// Traduction des filtres d'interface -> une requête SQL paramétrée unique.
// Chaque filtre actif ajoute une condition EXISTS sur le PV principal (ou ses extensions),
// ce qui permet de combiner librement les critères sans dupliquer les lignes.
export const normRef = s => (s || '').replace(/[\s.]/g, '').toUpperCase();
export const normTxt = s => (s || '').normalize('NFKD').replace(/[̀-ͯ]/g, '').toLowerCase();

const FILTRES = {
  reference: {
    sql: `EXISTS (SELECT 1 FROM v_document_rattachement r2 JOIN document_composant dc ON dc.document_id = r2.document_id
                  LEFT JOIN reference_composant rc ON rc.id = dc.reference_id
                  WHERE r2.pv_principal_id = pv.id AND (rc.reference_normalisee LIKE '%' || :reference || '%'
                    OR dc.reference_id IN (SELECT reference_id FROM reference_alias WHERE upper(replace(replace(alias,' ',''),'.','')) LIKE '%' || :reference || '%')))`,
    param: v => normRef(v),
  },
  systeme: { sql: `EXISTS (SELECT 1 FROM v_document_rattachement r2 JOIN document_systeme ds ON ds.document_id = r2.document_id WHERE r2.pv_principal_id = pv.id AND ds.systeme_id = :systeme)` },
  typologie: { sql: `EXISTS (SELECT 1 FROM configuration c WHERE c.document_id = pv.id AND c.typologie_code = :typologie)` },
  duree: { param: Number, sql: `EXISTS (SELECT 1 FROM v_document_rattachement r2 JOIN v_classement_feu f ON f.document_id = r2.document_id WHERE r2.pv_principal_id = pv.id AND f.duree_min >= :duree
                  AND (:critere = '' OR (:critere = 'I' AND f.critere_i = 1) OR (:critere = 'W' AND f.critere_w = 1)))`, extra: { critere: '' } },
  categorie: { sql: `EXISTS (SELECT 1 FROM v_document_rattachement r2 JOIN document_composant dc ON dc.document_id = r2.document_id WHERE r2.pv_principal_id = pv.id AND dc.categorie_code = :categorie)` },
  fonction: { sql: `EXISTS (SELECT 1 FROM v_document_rattachement r2 JOIN document_composant dc ON dc.document_id = r2.document_id JOIN dc_serrure s ON s.document_composant_id = dc.id
                    WHERE r2.pv_principal_id = pv.id AND s.fonction_code = :fonction)` },
  largeur: { sql: `EXISTS (SELECT 1 FROM dimension_format df JOIN dimension dm ON dm.format_id = df.id JOIN v_document_rattachement r2 ON r2.document_id = df.document_id
                   WHERE r2.pv_principal_id = pv.id AND df.objet_code IN ('passage_libre','vantail_hors_tout','vitrage_hors_tout','vitrage_clair','cloison')
                   AND dm.grandeur_code = 'largeur' AND dm.nature_code = 'autorise_max' AND (dm.sans_limite = 1 OR dm.valeur_norm >= :largeur))`, param: Number },
  hauteur: { sql: `EXISTS (SELECT 1 FROM dimension_format df JOIN dimension dm ON dm.format_id = df.id JOIN v_document_rattachement r2 ON r2.document_id = df.document_id
                   WHERE r2.pv_principal_id = pv.id AND df.objet_code IN ('passage_libre','vantail_hors_tout','vitrage_hors_tout','vitrage_clair','cloison','facade_entre_dalles')
                   AND dm.grandeur_code = 'hauteur' AND dm.nature_code = 'autorise_max' AND (dm.sans_limite = 1 OR dm.valeur_norm >= :hauteur))`, param: Number },
  texte: { sql: `EXISTS (SELECT 1 FROM v_document_rattachement r2 JOIN recherche_index ri ON ri.document_id = r2.document_id WHERE r2.pv_principal_id = pv.id AND ri.texte LIKE '%' || :texte || '%')`, param: normTxt },
  valide: { sql: `ve.date_validite_effective >= :valide` },
};

export function buildQuery(state) {
  const where = [`pv.type_code = 'pv_classement'`, `pv.present_dans_corpus = 1`];
  const params = {};
  for (const [k, def] of Object.entries(FILTRES)) {
    const v = state[k];
    if (v === undefined || v === null || v === '') continue;
    where.push(def.sql);
    params[':' + k] = def.param ? def.param(v) : v;
    if (def.extra) for (const [ek, ev] of Object.entries(def.extra)) params[':' + ek] = state[ek] ?? ev;
  }
  const sql = `SELECT pv.id, pv.numero_normalise, pv.objet, ve.date_validite_effective, ve.derniere_reconduction,
      (SELECT group_concat(DISTINCT s.nom) FROM document_systeme ds JOIN systeme s ON s.id = ds.systeme_id WHERE ds.document_id = pv.id AND ds.role = 'principal') AS systemes,
      (SELECT group_concat(DISTINCT f.classe_normalisee) FROM v_document_rattachement r2 JOIN performance f ON f.document_id = r2.document_id WHERE r2.pv_principal_id = pv.id) AS classements,
      (SELECT count(*) FROM document_relation dr WHERE dr.document_cible_id = pv.id AND dr.type_relation_code = 'etend') AS nb_extensions,
      (SELECT count(*) FROM controle_humain ch JOIN v_document_rattachement r2 ON r2.document_id = ch.document_id WHERE r2.pv_principal_id = pv.id AND ch.statut = 'ouvert') AS nb_controles
    FROM document pv LEFT JOIN v_validite_effective ve ON ve.document_id = pv.id
    WHERE ${where.join('\n  AND ')}
    ORDER BY pv.numero_normalise`;
  return { sql, params };
}
