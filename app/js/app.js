import { openDatabase, all } from './db.js';
import { buildQuery } from './filters.js';

const $ = s => document.querySelector(s);
const esc = v => v == null ? '' : String(v).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
let DB;

function fillSelect(sel, rows, label = r => r.libelle) {
  for (const r of rows) sel.insertAdjacentHTML('beforeend', `<option value="${esc(r.code)}">${esc(label(r))}</option>`);
}

function table(rows, cols) {
  if (!rows.length) return '<p class="vide">Aucune donnée.</p>';
  cols = cols || Object.keys(rows[0]);
  return `<table><thead><tr>${cols.map(c => `<th>${esc(c)}</th>`).join('')}</tr></thead><tbody>${
    rows.map(r => `<tr>${cols.map(c => `<td>${esc(r[c])}</td>`).join('')}</tr>`).join('')}</tbody></table>`;
}

function state() {
  const f = new FormData($('#filtres'));
  return Object.fromEntries([...f.entries()].map(([k, v]) => [k, String(v).trim()]));
}

function run() {
  const { sql, params } = buildQuery(state());
  $('#sql').textContent = sql + '\n\n-- paramètres : ' + JSON.stringify(params);
  const rows = all(DB, sql, params);
  $('#compte').textContent = `${rows.length} PV`;
  $('#resultats').innerHTML = rows.map(r => `
    <article class="carte" data-id="${esc(r.id)}">
      <h3>${esc(r.numero_normalise)} <span class="classes">${esc(r.classements || '')}</span></h3>
      <p>${esc(r.objet)}</p>
      <p class="meta">Système : ${esc(r.systemes || '—')} · Valide jusqu'au ${esc(r.date_validite_effective || '—')}
        ${r.derniere_reconduction ? '(' + esc(r.derniere_reconduction) + ')' : ''} · ${r.nb_extensions} extension(s)
        ${r.nb_controles ? `· <span class="alerte">${r.nb_controles} point(s) à vérifier</span>` : ''}</p>
    </article>`).join('');
}

function detail(id) {
  const q = (sql, p = {}) => all(DB, sql, { ':id': id, ...p });
  const docs = `SELECT document_id FROM v_document_rattachement WHERE pv_principal_id = :id`;
  $('#detail').innerHTML = `
    <button id="fermer">× Fermer</button>
    <h2>${esc(q('SELECT numero_normalise FROM document WHERE id = :id')[0].numero_normalise)}</h2>
    <h3>Documents liés</h3>${table(q(`SELECT dr.type_relation_code AS relation, s.numero_normalise AS source, c.numero_normalise AS cible, s.date_emission, s.present_dans_corpus AS fourni, dr.commentaire
       FROM document_relation dr JOIN document s ON s.id = dr.document_source_id JOIN document c ON c.id = dr.document_cible_id
       WHERE dr.document_cible_id = :id OR dr.document_source_id = :id OR dr.document_source_id IN (${docs})`))}
    <h3>Classements</h3>${table(q(`SELECT numero_normalise AS document, configuration, classe_normalisee AS classe, sens_feu, condition_texte, page_doc AS page FROM v_classement_feu WHERE document_id IN (${docs})`))}
    <h3>Restrictions</h3>${table(q(`SELECT r.type_code AS type, r.libelle, d.numero_normalise AS document, sp.page_doc AS page FROM restriction r JOIN document d ON d.id = r.document_id LEFT JOIN source_page sp ON sp.id = r.source_page_id WHERE r.document_id IN (${docs})`))}
    <h3>Dimensions autorisées</h3>${table(q(`SELECT numero_normalise AS document, libelle, grandeur_code AS grandeur, operateur_code AS op, valeur_origine AS valeur, unite_origine AS unite, statut_extraction AS statut, page_doc AS page FROM v_dimension WHERE document_id IN (${docs}) ORDER BY format_id`))}
    <h3>Composants</h3>${table(q(`SELECT numero_normalise AS document, reference_brute AS ref, fabricant, categorie_code AS categorie, role_code AS role, statut_autorisation_code AS statut, designation_document AS designation, page_doc AS page, planche, statut_extraction AS extraction FROM v_composant WHERE document_id IN (${docs}) AND parent_id IS NULL`))}
    <h3>Points de contrôle humain</h3>${table(q(`SELECT ch.type_code AS type, ch.description FROM controle_humain ch WHERE ch.document_id IN (${docs}) AND ch.statut = 'ouvert'`))}`;
  $('#detail').hidden = false;
  $('#fermer').onclick = () => { $('#detail').hidden = true; };
}

async function init() {
  try {
    const { db, meta } = await openDatabase(m => { $('#statut').textContent = m; });
    DB = db;
    $('#statut').textContent = `Base v${meta.schema_version} · générée le ${meta.genere_le}`;
    fillSelect($('[name=systeme]'), all(DB, 'SELECT id AS code, nom AS libelle FROM systeme ORDER BY nom'));
    fillSelect($('[name=typologie]'), all(DB, 'SELECT code, libelle FROM ref_typologie'));
    fillSelect($('[name=categorie]'), all(DB, 'SELECT DISTINCT r.code, r.libelle FROM ref_categorie_composant r JOIN document_composant dc ON dc.categorie_code = r.code ORDER BY r.libelle'));
    fillSelect($('[name=fonction]'), all(DB, 'SELECT code, code AS libelle FROM ref_fonction_serrure'));
    $('#filtres').addEventListener('input', run);
    $('#resultats').addEventListener('click', e => { const c = e.target.closest('.carte'); if (c) detail(c.dataset.id); });
    run();
  } catch (e) {
    $('#statut').textContent = 'Erreur : ' + e.message;
  }
}
init();
