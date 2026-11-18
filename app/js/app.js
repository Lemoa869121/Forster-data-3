import { openDatabase, all } from './db.js';
import { buildQuery, facetQuery, hitsQuery, dimInconnueQuery, FACETTES, PREPARATION, LIBELLES_VERRIER, normRef } from './filters.js';

const $ = s => document.querySelector(s);
const $$ = s => [...document.querySelectorAll(s)];
const esc = v => v == null ? '' : String(v).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const MULTI = ['systeme', 'typologie', 'verrier', 'support', 'type_vitrage'];
const DEFAUTS = { etat: 'valide', type_doc: 'pv_classement', vantaux: '', critere: '', duree: '', objet_dim: 'passage' };
const LIB_FILTRE = { reference: 'Réf.', texte: 'Texte', vantaux: 'Vantaux', critere: 'Critère', duree: 'Durée ≥', gamme: 'Vitrage', categorie: 'Composant',
  fonction: 'Fonction', largeur: 'Largeur ≥', hauteur: 'Hauteur ≥', valide: 'Valide au', classe_lue: 'Classe lue', antipanique: 'Antipanique',
  allege: 'Allège', verifie: 'Relus seulement', etat: 'État', type_doc: 'Type', dim_inconnue: 'Dimension non renseignée incluse', objet_dim: 'Dimension sur' };
let DB, lignes = [], libelles = {};

const q = (sql, params = {}) => all(DB, sql, params);

function lireEtat() {
  const f = new FormData($('#filtres'));
  const s = {};
  for (const [k, v] of f.entries()) if (!MULTI.includes(k)) s[k] = String(v).trim();
  for (const k of MULTI) s[k] = f.getAll(k).map(String);
  return s;
}

function ecrireEtat(s) {
  for (const el of $$('#filtres input, #filtres select')) {
    const v = s[el.name];
    if (el.type === 'checkbox') el.checked = Array.isArray(v) ? v.includes(el.value) : v === el.value;
    else if (el.type === 'radio') el.checked = (v ?? DEFAUTS[el.name] ?? '') === el.value;
    else el.value = v ?? DEFAUTS[el.name] ?? '';
  }
}

function versHash(s) {
  const u = new URLSearchParams();
  for (const [k, v] of Object.entries(s)) {
    if (Array.isArray(v)) v.forEach(x => u.append(k, x));
    else if (v && v !== DEFAUTS[k]) u.set(k, v);
  }
  const tri = $('#tri').value; if (tri !== 'numero') u.set('tri', tri);
  history.replaceState(null, '', '#' + u.toString());
}

function depuisHash() {
  const u = new URLSearchParams(location.hash.slice(1));
  const s = { ...DEFAUTS };
  for (const k of MULTI) s[k] = u.getAll(k);
  for (const [k, v] of u.entries()) if (!MULTI.includes(k) && k !== 'tri') s[k] = v;
  if (u.get('tri')) $('#tri').value = u.get('tri');
  return s;
}

// --- Facettes : options avec compteurs, tenant compte des autres filtres ---
function majFacettes(s) {
  for (const nom of FACETTES) {
    const { sql, params } = facetQuery(nom, s);
    const compte = Object.fromEntries(q(sql, params).map(r => [r.code, r.n]));
    const conteneur = $(`[data-facette="${nom}"]`);
    if (conteneur) {
      conteneur.innerHTML = Object.entries(libelles[nom]).map(([code, lib]) => {
        const n = compte[code] || 0, coche = s[nom].includes(code);
        return `<label class="puce${n || coche ? '' : ' vide'}"><input type="checkbox" name="${nom}" value="${esc(code)}"${coche ? ' checked' : ''}><span>${esc(lib)} <small>${n}</small></span></label>`;
      }).join('');
    }
    const select = $(`[data-facette-select="${nom}"]`);
    if (select) {
      const v = s[nom === 'gamme' ? 'gamme' : nom];
      select.innerHTML = `<option value="">Toutes</option>` + Object.entries(libelles[nom]).map(([code, lib]) =>
        `<option value="${esc(code)}"${code === v ? ' selected' : ''}${compte[code] ? '' : ' disabled'}>${esc(lib)} (${compte[code] || 0})</option>`).join('');
    }
  }
}

function etatValidite(d) {
  if (!d) return '';
  const auj = new Date().toISOString().slice(0, 10);
  const dans1an = new Date(Date.now() + 365 * 864e5).toISOString().slice(0, 10);
  if (d < auj) return '<span class="badge echu">échu</span>';
  if (d <= dans1an) return '<span class="badge bientot">échéance &lt; 12 mois</span>';
  return '';
}

function classes(txt) {
  const l = (txt || '').split(',').filter(Boolean);
  const lues = new Set(l.filter(c => !c.endsWith('*')));
  return [...new Set(l)].filter(c => !(c.endsWith('*') && lues.has(c.slice(0, -1)))).sort().map(c => c.endsWith('*')
    ? `<span class="classe fichier" title="Classe reprise du nom de fichier, non lue dans le PV">${esc(c.slice(0, -1))}</span>`
    : `<span class="classe">${esc(c)}</span>`).join(' ');
}

function puceActives(s) {
  const p = [];
  for (const [k, v] of Object.entries(s)) {
    if (MULTI.includes(k)) v.forEach(x => p.push([k, x, `${(libelles[k] || {})[x] || x}`]));
    else if (v && v !== DEFAUTS[k] && LIB_FILTRE[k]) p.push([k, v, `${LIB_FILTRE[k]} : ${v === '1' ? 'oui' : v}`]);
  }
  $('#actifs').innerHTML = p.map(([k, v, l]) => `<span class="actif">${esc(l)}<button type="button" data-k="${esc(k)}" data-v="${esc(v)}" aria-label="Retirer ${esc(l)}">×</button></span>`).join('');
}

function run() {
  const s = lireEtat();
  versHash(s);
  majFacettes(s);
  puceActives(s);
  const { sql, params } = buildQuery(s, $('#tri').value);
  $('#sql').textContent = sql + '\n\n-- paramètres : ' + JSON.stringify(params);
  lignes = q(sql, params);
  $('#compte').textContent = `${lignes.length} PV`;
  if (!lignes.length) { $('#resultats').innerHTML = `<div class="vide-res">Aucun PV ne correspond. Retirez un filtre (puces ci-dessus)${s.largeur || s.hauteur ? ', ou cochez « Inclure les PV où cette dimension n\'a pas été extraite » (les dimensions ne sont pas encore extraites pour tous les PV)' : ''}.</div>`; return; }
  $('#resultats').innerHTML = lignes.map(r => {
    let trouve = '';
    if (s.reference) {
      const h = hitsQuery(r.id, s.reference);
      const hits = q(h.sql, h.params);
      if (hits.length) trouve = `<div class="trouve">Trouvé : ${hits.map(x => `<b>${esc(x.ref)}</b> (${esc(x.cat)}) — ${esc(x.doc)}${x.planche ? ', ' + esc(x.planche) : x.page ? ', p. ' + esc(x.page) : ''}`).join(' · ')}</div>`;
    }
    if ((s.largeur || s.hauteur) && s.dim_inconnue) {
      const d = dimInconnueQuery(r.id, s.objet_dim); if (!q(d.sql, d.params)[0].n) trouve += '<div class="trouve">Dimension non renseignée dans la base pour ce PV : à vérifier sur l\'original.</div>';
    }
    return `<article class="carte" tabindex="0" data-id="${esc(r.id)}">
      <div class="l1"><span class="num">${esc(r.numero_normalise)}</span> ${classes(r.classements)}
        ${r.auto ? '<span class="badge auto">extraction automatique — à vérifier</span>' : '<span class="badge relu">saisie relue</span>'} ${etatValidite(r.validite)}</div>
      <div class="objet">${esc(r.objet || '')}</div>
      <div class="meta"><span>${esc(r.systemes || 'Système non identifié')}</span>${r.verrier ? `<span>${esc(LIBELLES_VERRIER[r.verrier] || r.verrier)}</span>` : ''}
        <span>Valide jusqu'au ${esc(r.validite || '—')}${r.derniere_reconduction ? ' (' + esc(r.derniere_reconduction) + ')' : ''}</span>
        <span>${r.nb_extensions} extension(s)</span>${r.nb_controles ? `<span>${r.nb_controles} point(s) à vérifier</span>` : ''}</div>${trouve}
    </article>`;
  }).join('');
}

// --- Fiche PV en onglets ---
function table(rows, cols, marque = null) {
  if (!rows.length) return '<p class="note">Aucune donnée.</p>';
  cols = cols || Object.keys(rows[0]).filter(c => c !== '_statut');
  return `<table><thead><tr>${cols.map(c => `<th>${esc(c)}</th>`).join('')}</tr></thead><tbody>${
    rows.map(r => `<tr class="${r._statut && r._statut !== 'extrait' ? 'a-verifier' : ''}">${cols.map(c => `<td>${esc(r[c])}</td>`).join('')}</tr>`).join('')}</tbody></table>`;
}

function detail(id) {
  const p = { ':id': id };
  const docs = `SELECT document_id FROM rat WHERE pv_principal_id = :id`;
  const pv = q(`SELECT d.*, f.nom_fichier, f.url FROM document d LEFT JOIN fichier_source f ON f.id = d.fichier_source_id WHERE d.id = :id`, p)[0];
  const ong = {
    'Synthèse': () => `
      ${pv.fichier_source_id && pv.fichier_source_id.startsWith('FIC-AUTO') ? '<div class="ancre-avert">Ce PV provient de l\'extraction automatique (OCR) : toutes les données sont à vérifier sur l\'original.</div>' : ''}
      <p><b>${esc(pv.objet || '')}</b></p>
      <p class="note">Fichier : ${esc(pv.nom_fichier || '—')}${pv.url ? ` · <a href="${esc(pv.url)}" target="_blank" rel="noopener">ouvrir le PDF</a>` : ''}</p>
      <h3>Classements</h3>${table(q(`SELECT numero_normalise AS document, configuration, classe_normalisee AS classe, sens_feu, condition_texte AS condition, page_doc AS page, statut_extraction AS _statut FROM v_classement_feu WHERE document_id IN (${docs})`, p))}
      <h3>Documents liés</h3>${table(q(`SELECT dr.type_relation_code AS relation, s.numero_normalise AS source, c.numero_normalise AS cible, s.date_emission AS emission, s.date_validite AS validite,
          CASE s.present_dans_corpus WHEN 1 THEN 'oui' ELSE 'non fourni' END AS fourni, dr.commentaire
          FROM document_relation dr JOIN document s ON s.id = dr.document_source_id JOIN document c ON c.id = dr.document_cible_id
          WHERE dr.document_cible_id = :id OR dr.document_source_id = :id OR dr.document_source_id IN (${docs}) ORDER BY s.date_emission`, p))}`,
    'Composants': () => `<label class="champ" style="max-width:320px">Filtrer cette liste<input type="search" id="filtre-comp" placeholder="référence, catégorie, mot…"></label>
      <div id="liste-comp">${table(q(`SELECT v.numero_normalise AS document, v.reference_brute AS "référence", v.fabricant, c.libelle AS "catégorie", ro.libelle AS "rôle",
          sa.libelle AS statut, v.designation_document AS "désignation / contexte", coalesce(v.planche, 'p. ' || v.page_doc) AS source, v.statut_extraction AS _statut
          FROM v_composant v JOIN ref_categorie_composant c ON c.code = v.categorie_code JOIN ref_role_composant ro ON ro.code = v.role_code
          JOIN ref_statut_autorisation sa ON sa.code = v.statut_autorisation_code
          WHERE v.document_id IN (${docs}) AND v.parent_id IS NULL ORDER BY c.famille, c.libelle, v.reference_brute`, p))}</div>`,
    'Dimensions': () => `<p class="note">Limites du domaine de validité (valeurs autorisées). Les valeurs mesurées en essai ne figurent jamais ici.</p>` + table(q(`SELECT v.numero_normalise AS document, v.libelle, g.libelle AS grandeur, o.libelle AS "opérateur", v.valeur_origine AS valeur, v.unite_origine AS "unité",
          v.page_doc AS page, v.statut_extraction AS _statut FROM v_dimension v JOIN ref_grandeur g ON g.code = v.grandeur_code JOIN ref_operateur o ON o.code = v.operateur_code
          WHERE v.document_id IN (${docs}) ORDER BY v.format_id`, p)),
    'Mise en œuvre': () => `<h3>Constructions support</h3>${table(q(`SELECT d.numero_normalise AS document, t.libelle AS support, s.masse_vol_min_kg_m3 AS "masse vol. min", s.epaisseur_min_mm AS "ép. min",
          s.classement_pv_exige AS "PV exigé", s.allege_autorisee AS allège, s.condition_texte AS condition FROM support_pose s JOIN document d ON d.id = s.document_id
          JOIN ref_type_support t ON t.code = s.type_support_code WHERE s.document_id IN (${docs})`, p))}
      <h3>Restrictions et conditions</h3>${table(q(`SELECT t.libelle AS type, r.libelle, d.numero_normalise AS document FROM restriction r JOIN document d ON d.id = r.document_id
          JOIN ref_type_restriction t ON t.code = r.type_code WHERE r.document_id IN (${docs}) ORDER BY t.libelle`, p))}`,
    'À vérifier': () => table(q(`SELECT d.numero_normalise AS document, t.libelle AS type, ch.description FROM controle_humain ch JOIN document d ON d.id = ch.document_id
          JOIN ref_type_controle t ON t.code = ch.type_code WHERE ch.document_id IN (${docs}) AND ch.statut = 'ouvert'`, p)),
  };
  const nb = {
    'Composants': q(`SELECT count(*) n FROM document_composant WHERE document_id IN (${docs}) AND parent_id IS NULL`, p)[0].n,
    'Dimensions': q(`SELECT count(*) n FROM dimension_format WHERE document_id IN (${docs})`, p)[0].n,
    'À vérifier': q(`SELECT count(*) n FROM controle_humain WHERE document_id IN (${docs}) AND statut = 'ouvert'`, p)[0].n,
  };
  const el = $('#detail');
  el.innerHTML = `<div class="detail-tete"><h2>${esc(pv.numero_normalise)}</h2>${pv.fichier_source_id && pv.fichier_source_id.startsWith('FIC-AUTO') ? '<span class="badge auto">à vérifier</span>' : '<span class="badge relu">saisie relue</span>'}
      <button class="fermer" type="button">Fermer</button></div>
    <div class="onglets" role="tablist">${Object.keys(ong).map((k, i) => `<button role="tab" aria-selected="${i === 0}" data-o="${esc(k)}">${esc(k)}${nb[k] != null ? ` <small>${nb[k]}</small>` : ''}</button>`).join('')}</div>
    <div class="contenu" id="contenu"></div>`;
  const montrer = k => {
    $$('.onglets button').forEach(b => b.setAttribute('aria-selected', b.dataset.o === k));
    $('#contenu').innerHTML = ong[k]();
    const fc = $('#filtre-comp');
    if (fc) fc.oninput = () => { const t = fc.value.toLowerCase(); $$('#liste-comp tbody tr').forEach(tr => { tr.hidden = t && !tr.textContent.toLowerCase().includes(t); }); };
  };
  el.querySelector('.onglets').onclick = e => { const b = e.target.closest('button'); if (b) montrer(b.dataset.o); };
  el.querySelector('.fermer').onclick = () => { el.hidden = true; };
  el.hidden = false;
  montrer('Synthèse');
}

function exporterCSV() {
  const cols = ['numero_normalise', 'classements', 'systemes', 'verrier', 'validite', 'derniere_reconduction', 'nb_extensions', 'auto', 'objet', 'nom_fichier'];
  const lignesCSV = [cols.join(';'), ...lignes.map(r => cols.map(c => `"${String(r[c] ?? '').replace(/"/g, '""')}"`).join(';'))];
  const a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob(['﻿' + lignesCSV.join('\n')], { type: 'text/csv;charset=utf-8' }));
  a.download = 'pv-forster-selection.csv'; a.click();
}

async function init() {
  try {
    const { db, meta } = await openDatabase(m => { $('#statut').textContent = m; });
    DB = db;
    DB.exec(PREPARATION);
    const nbPv = q(`SELECT count(*) n FROM document WHERE type_code = 'pv_classement' AND present_dans_corpus = 1`)[0].n;
    $('#statut').textContent = `${nbPv} PV · base du ${String(meta.genere_le).slice(0, 10)}`;
    // libellés stables des facettes (toutes les options existantes)
    const vide = { systeme: [], typologie: [], verrier: [], support: [], type_vitrage: [], etat: '' };
    for (const nom of FACETTES) {
      const { sql, params } = facetQuery(nom, vide);
      libelles[nom] = Object.fromEntries(q(sql, params).map(r => [r.code, nom === 'verrier' ? (LIBELLES_VERRIER[r.code] || r.code) : r.libelle]));
    }
    $('[name=fonction]').insertAdjacentHTML('beforeend', q('SELECT code FROM ref_fonction_serrure').map(r => `<option>${esc(r.code)}</option>`).join(''));
    $('#liste-refs').innerHTML = q(`SELECT rc.reference_normalisee AS r, coalesce(o.nom,'') AS f FROM reference_composant rc LEFT JOIN organisme o ON o.id = rc.fabricant_id
        WHERE rc.id IN (SELECT reference_id FROM document_composant) ORDER BY 1 LIMIT 3000`).map(x => `<option value="${esc(x.r)}">${esc(x.f)}</option>`).join('');
    ecrireEtat(depuisHash());
    let minuterie;
    $('#filtres').addEventListener('input', e => { clearTimeout(minuterie); minuterie = setTimeout(run, e.target.type === 'search' || e.target.type === 'number' ? 250 : 0); });
    $('#tri').addEventListener('change', run);
    $('#reinit').onclick = () => { ecrireEtat({ ...DEFAUTS, systeme: [], typologie: [], verrier: [], support: [], type_vitrage: [] }); run(); };
    $('#actifs').onclick = e => {
      const b = e.target.closest('button'); if (!b) return;
      const s = lireEtat(); const k = b.dataset.k;
      if (MULTI.includes(k)) s[k] = s[k].filter(x => x !== b.dataset.v); else s[k] = DEFAUTS[k] ?? '';
      ecrireEtat(s); run();
    };
    $('#resultats').addEventListener('click', e => { const c = e.target.closest('.carte'); if (c) detail(c.dataset.id); });
    $('#resultats').addEventListener('keydown', e => { const c = e.target.closest('.carte'); if (c && e.key === 'Enter') detail(c.dataset.id); });
    document.addEventListener('keydown', e => { if (e.key === 'Escape') $('#detail').hidden = true; });
    $('#export').onclick = exporterCSV;
    $('#partager').onclick = async () => { try { await navigator.clipboard.writeText(location.href); $('#partager').textContent = 'Lien copié'; setTimeout(() => { $('#partager').textContent = 'Copier le lien'; }, 1500); } catch (_) { prompt('Lien :', location.href); } };
    run();
  } catch (e) {
    $('#statut').textContent = 'Erreur : ' + e.message;
    console.error(e);
  }
}
init();
