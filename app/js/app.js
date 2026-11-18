import { openDatabase, all } from './db.js';
import { buildQuery, facetQuery, hitsQuery, dimInconnueQuery, FACETTES, PREPARATION, LIBELLES_VERRIER, normRef, normTxt, COMPLEMENTS } from './filters.js';

const $ = s => document.querySelector(s);
const $$ = s => [...document.querySelectorAll(s)];
const esc = v => v == null ? '' : String(v).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const MULTI = ['systeme', 'typologie', 'verrier', 'support', 'type_vitrage', 'complement', 'domaine', 'cumul_fd'];
const DEFAUTS = { etat: 'valide', type_doc: 'pv_classement', vantaux: '', critere: '', duree: '', objet_dim: 'passage' };
const LIB_FILTRE = { reference: 'Réf.', texte: 'Texte', vantaux: 'Vantaux', critere: 'Critère', duree: 'Durée ≥', gamme: 'Vitrage', categorie: 'Composant',
  fonction: 'Fonction', largeur: 'Largeur ≥', hauteur: 'Hauteur ≥', valide: 'Valide au', classe_lue: 'Classe lue', antipanique: 'Antipanique',
  allege: 'Allège', verifie: 'Relus seulement', cumul: 'Cumul feu énoncé', etat: 'État', type_doc: 'Type', dim_inconnue: 'Dimension non renseignée incluse', objet_dim: 'Dimension sur' };
const PAGE = 25;
let DB, lignes = [], libelles = {};
const q = (sql, params = {}) => all(DB, sql, params);

/* ---------- Catégories (inspirées de ForsterData) ---------- */
const ICONE = {
  feu: '<svg viewBox="0 0 24 24"><path d="M12 22c4 0 7-2.7 7-6.8 0-3.4-2.3-5.6-3.6-7.6-.4 1.6-1.3 2.7-2.4 3.2C13.3 7 11.6 4 9 2c.3 3-1.6 5.2-3 7.1C4.8 10.8 5 12.7 5 15.2 5 19.3 8 22 12 22z"/></svg>',
  rc: '<svg viewBox="0 0 24 24"><rect x="4" y="10" width="16" height="11" rx="2"/><path d="M8 10V7a4 4 0 0 1 8 0v3"/><circle cx="12" cy="15.5" r="1.4"/></svg>',
  fb: '<svg viewBox="0 0 24 24"><path d="M12 3l8 3v6c0 4.5-3.4 8-8 9-4.6-1-8-4.5-8-9V6z"/><path d="M9 12l2 2 4-4"/></svg>',
  aev: '<svg viewBox="0 0 24 24"><path d="M3 8h11a3 3 0 1 0-3-3"/><path d="M3 12h15a3 3 0 1 1-3 3"/><path d="M3 16h7"/></svg>',
  acoustique: '<svg viewBox="0 0 24 24"><path d="M4 9v6h4l5 4V5L8 9z"/><path d="M17 9l4 6M21 9l-4 6"/></svg>',
  rapports: '<svg viewBox="0 0 24 24"><path d="M6 2h9l5 5v15H6z"/><path d="M14 2v6h6M9 13h8M9 17h8"/></svg>',
};
const CATS = {
  feu: { label: 'Feu', groupe: 'Sécurité', aide: 'Procès-verbaux de classement (corpus PDF)' },
  rc: { label: 'Anti-effraction', groupe: 'Sécurité', aide: 'Fiches ForsterData' },
  fb: { label: 'Pare-balles', groupe: 'Sécurité', aide: 'Fiches ForsterData' },
  aev: { label: 'AEV', groupe: 'Performances', aide: 'Fiches ForsterData' },
  acoustique: { label: 'Acoustique', groupe: 'Performances', aide: 'Fiches ForsterData' },
  rapports: { label: "Rapports d'essais", groupe: 'Performances', aide: 'Tous domaines, extraction automatique' },
};
const SECU_LIB = { feu: 'Feu', rc: 'Anti-effraction', fb: 'Pare-balles' };
const ORDRE = c => { const m = String(c).match(/^(EI|EW|E|RC|FB)\s?(\d+)(?:-(NS|S))?/); return m ? ({ E: 0, EW: 500, EI: 1000, RC: 2000, FB: 3000 }[m[1]] + (+m[2]) * 2 + (m[3] === 'S' ? 1 : 0)) : 9999; };
const trierClasses = l => [...new Set(l.filter(Boolean))].sort((a, b) => ORDRE(a) - ORDRE(b) || String(a).localeCompare(b));

// Colonnes et filtres des catégories « fiches » et « rapports » (filtrage en mémoire, comme ForsterData)
const COLS = {
  rc: [['type_chassis', 'Type de châssis', 1], ['classe', 'Classe'], ['serie', 'Série'], ['numero_pv', 'PV'], ['cumul_txt', 'Cumul feu / FB'], ['doc_etat', 'Corpus']],
  fb: [['type_chassis', 'Type de châssis', 1], ['classe', 'Classe'], ['serie', 'Série'], ['numero_pv', 'PV'], ['cumul_txt', 'Cumul feu / RC'], ['doc_etat', 'Corpus']],
  aev: [['type_chassis', 'Type de châssis', 1], ['serie', 'Série'], ['classe_air', 'A'], ['classe_eau', 'E'], ['classe_vent', 'V'], ['numero_pv', 'PV'], ['doc_etat', 'Corpus']],
  acoustique: [['type_chassis', 'Type de châssis', 1], ['serie', 'Série'], ['rw_db', 'Rw (dB)'], ['c_db', 'C'], ['ctr_db', 'Ctr'], ['numero_pv', 'PV'], ['doc_etat', 'Corpus']],
  rapports: [['numero_normalise', 'N°', 1], ['domaine_lib', 'Domaine'], ['perfs', 'Classes'], ['systemes', 'Système'], ['typologie', 'Typologie'], ['laboratoire', 'Laboratoire'], ['date_emission', 'Date']],
};
const FILTRES_CAT = {
  rc: [['recherche'], ['chips', 'classe', 'Classe'], ['select', 'type_chassis', 'Application'], ['chips', 'serie', 'Série'], ['cumul'], ['corpus']],
  fb: [['recherche'], ['chips', 'classe', 'Classe'], ['select', 'type_chassis', 'Application'], ['chips', 'serie', 'Série'], ['cumul'], ['corpus']],
  aev: [['recherche'], ['select', 'type_chassis', 'Type de châssis'], ['chips', 'serie', 'Série'], ['min', 'classe_air', "Perméabilité à l'air (A) minimum", ['A1', 'A2', 'A3', 'A4']],
    ['min', 'classe_eau', "Étanchéité à l'eau (E) minimum", ['E1A', 'E2A', 'E3A', 'E4A', 'E5A', 'E6A', 'E7A', 'E8A', 'E9A']], ['min', 'classe_vent', 'Résistance au vent (V) minimum', ['V1', 'V2', 'V3', 'V4', 'V5']], ['corpus']],
  acoustique: [['recherche'], ['select', 'type_chassis', 'Type de châssis'], ['chips', 'serie', 'Série'], ['nummin', 'rw_db', 'Affaiblissement Rw minimum (dB)'], ['corpus']],
  rapports: [['recherche'], ['chips', 'domaine_lib', 'Domaine'], ['chips', 'systemes', 'Système', 1], ['chips', 'typologie', 'Typologie'], ['select', 'type_lib', 'Type de document'], ['select', 'laboratoire', 'Laboratoire']],
};
const etat = { cat: 'feu', page: 1, tri: null, cmp: new Map(), F: {} };
const DONNEES = {};
const vide = () => ({ q: '', chips: {}, sel: {}, min: {}, nummin: {}, cumul: {}, corpus: false });

/* ---------- État du formulaire feu ---------- */
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
  u.set('cat', etat.cat);
  if (etat.cat === 'feu') {
    for (const [k, v] of Object.entries(s)) {
      if (Array.isArray(v)) v.forEach(x => u.append(k, x));
      else if (v && v !== DEFAUTS[k]) u.set(k, v);
    }
    const tri = $('#tri').value; if (tri !== 'numero') u.set('tri', tri);
  } else if (JSON.stringify(etat.F) !== JSON.stringify(vide())) u.set('f', JSON.stringify(etat.F));
  history.replaceState(null, '', '#' + u.toString());
}
function depuisHash() {
  const h = location.hash.slice(1);
  const u = new URLSearchParams(h.includes('=') ? h : 'cat=' + (h || 'feu'));
  etat.cat = CATS[u.get('cat')] ? u.get('cat') : 'feu';
  etat.F = vide();
  if (u.get('f')) try { etat.F = { ...vide(), ...JSON.parse(u.get('f')) }; } catch (_) { /* lien abîmé : filtres ignorés */ }
  const s = { ...DEFAUTS };
  for (const k of MULTI) s[k] = u.getAll(k);
  for (const [k, v] of u.entries()) if (!MULTI.includes(k) && !['tri', 'cat', 'f'].includes(k)) s[k] = v;
  if (u.get('tri')) $('#tri').value = u.get('tri');
  return s;
}

/* ---------- Facettes du formulaire feu ---------- */
function majFacettes(s) {
  for (const nom of FACETTES) {
    const { sql, params } = facetQuery(nom, s);
    const compte = Object.fromEntries(q(sql, params).map(r => [r.code, r.n]));
    const conteneur = $(`[data-facette="${nom}"]`);
    if (conteneur) {
      conteneur.innerHTML = Object.entries(libelles[nom] || {}).map(([code, lib]) => {
        const n = compte[code] || 0, coche = (s[nom] || []).includes(code);
        return `<label class="puce${n || coche ? '' : ' vide'}"><input type="checkbox" name="${nom}" value="${esc(code)}"${coche ? ' checked' : ''}><span>${esc(lib)} <small>${n}</small></span></label>`;
      }).join('');
    }
    const select = $(`[data-facette-select="${nom}"]`);
    if (select) {
      const v = s[nom];
      select.innerHTML = `<option value="">Toutes</option>` + Object.entries(libelles[nom]).map(([code, lib]) =>
        `<option value="${esc(code)}"${code === v ? ' selected' : ''}${compte[code] ? '' : ' disabled'}>${esc(lib)} (${compte[code] || 0})</option>`).join('');
    }
  }
}

/* ---------- Badges ---------- */
function validite(d) {
  if (!d) return '<span class="badge b-na">—</span>';
  const auj = new Date().toISOString().slice(0, 10);
  const lim = new Date(Date.now() + 365 * 864e5).toISOString().slice(0, 10);
  const f = d.split('-').reverse().join('/');
  if (d < auj) return `<span class="badge b-bad" title="Expiré">Expiré ${f}</span>`;
  if (d <= lim) return `<span class="badge b-warn" title="Échéance à moins de 12 mois">${f}</span>`;
  return `<span class="badge b-ok">${f}</span>`;
}
function classes(txt) {
  const l = (txt || '').split(',').filter(Boolean);
  const lues = new Set(l.filter(c => !c.endsWith('*')));
  return [...new Set(l)].filter(c => !(c.endsWith('*') && lues.has(c.slice(0, -1)))).sort((a, b) => ORDRE(a) - ORDRE(b)).map(c => c.endsWith('*')
    ? `<span class="classe fichier" title="Classe reprise du nom de fichier, non lue dans le PV">${esc(c.slice(0, -1))}</span>`
    : `<span class="classe">${esc(c)}</span>`).join(' ');
}
const autres = txt => trierClasses((txt || '').split(',')).map(c => `<span class="classe autre">${esc(c)}</span>`).join(' ');

function puceActives(s) {
  const p = [];
  for (const [k, v] of Object.entries(s)) {
    if (MULTI.includes(k)) v.forEach(x => p.push([k, x, `${(libelles[k] || {})[x] || x}`]));
    else if (v && v !== DEFAUTS[k] && LIB_FILTRE[k]) p.push([k, v, `${LIB_FILTRE[k]} : ${v === '1' ? 'oui' : v}`]);
  }
  $('#actifs').innerHTML = p.map(([k, v, l]) => `<span class="actif">${esc(l)}<button type="button" data-k="${esc(k)}" data-v="${esc(v)}" aria-label="Retirer ${esc(l)}">×</button></span>`).join('');
}

/* ---------- Sélecteur de catégories ---------- */
function compteCat(c) {
  if (c === 'feu') return q(`SELECT count(*) n FROM document WHERE type_code = 'pv_classement' AND present_dans_corpus = 1`)[0].n;
  if (c === 'rapports') return q(`SELECT count(*) n FROM document WHERE id LIKE 'DOC-RAP-%'`)[0].n;
  return q(`SELECT count(*) n FROM fiche_forsterdata WHERE categorie = :c`, { ':c': c })[0].n;
}
function rendreGroupes() {
  const g = {};
  for (const [id, c] of Object.entries(CATS)) (g[c.groupe] ||= []).push(id);
  $('#groupes').innerHTML = Object.entries(g).map(([nom, ids]) => `<div class="groupe"><h2>${esc(nom)}</h2><div class="cats">${ids.map(id =>
    `<button class="cat" type="button" data-cat="${id}" aria-pressed="${etat.cat === id}">${ICONE[id]}<span><b>${esc(CATS[id].label)}</b><small>${esc(CATS[id].aide)}</small></span><span class="n">${CATS[id].n}</span></button>`).join('')}</div></div>`).join('');
}
function choisirCat(id) {
  if (etat.cat !== id) { etat.cmp.clear(); etat.F = vide(); }
  etat.cat = id; etat.page = 1; etat.tri = null;
  rendreGroupes(); rendreFiltresCat(); barreComparaison(); run();
}

/* ---------- Données des catégories en mémoire ---------- */
function donnees(cat) {
  if (DONNEES[cat]) return DONNEES[cat];
  if (cat === 'rapports') {
    DONNEES[cat] = q(`SELECT d.id, d.numero_normalise, d.objet, d.date_emission, d.type_code, dm.libelle AS domaine_lib, tdoc.libelle AS type_lib,
        o.nom AS laboratoire, (SELECT group_concat(DISTINCT p.classe_normalisee) FROM performance p WHERE p.document_id = d.id) AS perfs,
        (SELECT group_concat(DISTINCT s.nom) FROM document_systeme ds JOIN systeme s ON s.id = ds.systeme_id WHERE ds.document_id = d.id) AS systemes,
        (SELECT t.libelle FROM configuration c JOIN ref_typologie t ON t.code = c.typologie_code WHERE c.document_id = d.id LIMIT 1) AS typologie,
        (SELECT count(*) FROM cumul_performance cp WHERE cp.document_id = d.id) AS nb_cumuls
      FROM document d JOIN ref_domaine_performance dm ON dm.code = d.domaine_code JOIN ref_type_document tdoc ON tdoc.code = d.type_code
      LEFT JOIN organisme o ON o.id = d.laboratoire_id WHERE d.id LIKE 'DOC-RAP-%' ORDER BY d.domaine_code, d.numero_normalise`);
  } else {
    DONNEES[cat] = q(`SELECT f.*, d.numero_normalise AS doc_num, d.id AS doc_id,
        (SELECT group_concat(o.classe, '|') FROM lien_forsterdata l JOIN fiche_forsterdata o ON o.id = CASE WHEN l.fiche_a = f.id THEN l.fiche_b ELSE l.fiche_a END
          WHERE f.id IN (l.fiche_a, l.fiche_b)) AS liens,
        (SELECT group_concat(o.categorie || ':' || o.classe, '|') FROM lien_forsterdata l JOIN fiche_forsterdata o ON o.id = CASE WHEN l.fiche_a = f.id THEN l.fiche_b ELSE l.fiche_a END
          WHERE f.id IN (l.fiche_a, l.fiche_b)) AS liens_cat,
        (SELECT count(*) FROM controle_humain ch WHERE ch.ligne_id = f.id AND ch.statut = 'ouvert') AS nb_incoherences
      FROM fiche_forsterdata f LEFT JOIN document d ON d.id = f.document_pv_id WHERE f.categorie = :c ORDER BY f.id`, { ':c': cat });
    for (const r of DONNEES[cat]) {
      const parts = {};
      for (const x of (r.liens_cat || '').split('|').filter(Boolean)) { const [c, v] = x.split(':'); (parts[c] ||= []).push(v); }
      r.cumul = Object.fromEntries(Object.entries(parts).map(([c, v]) => [c, trierClasses(v)]));
      r.cumul_txt = ['feu', 'rc', 'fb'].filter(c => r.cumul[c]).map(c => r.cumul[c].join(' ')).join(' · ');
      r.doc_etat = r.document_pv_id ? (r.nb_incoherences ? '⚠ écart' : (r.rapprochement === 'exact' ? '✓' : '≈')) : '—';
    }
  }
  return DONNEES[cat];
}
const nombre = v => { const m = String(v ?? '').match(/\d+/); return m ? +m[0] : null; };

/* ---------- Filtres des catégories en mémoire ---------- */
function valeursUniques(rows, k, separer) {
  const v = rows.flatMap(r => separer ? String(r[k] || '').split(',') : [r[k]]).filter(x => x != null && x !== '' && x !== '-');
  return [...new Set(v.map(String))].sort((a, b) => a.localeCompare(b, 'fr', { numeric: true }));
}
function rendreFiltresCat() {
  const feu = etat.cat === 'feu';
  $('#filtres').hidden = !feu;
  $('#bloc-tri').hidden = !feu; $('#bloc-sql').hidden = !feu;
  const hote = $('#filtres-cat');
  if (feu) { hote.innerHTML = ''; return; }
  const rows = donnees(etat.cat), F = etat.F;
  hote.innerHTML = FILTRES_CAT[etat.cat].map(([type, k, lib, opt]) => {
    if (type === 'recherche') return `<div class="f"><label for="fq">Recherche</label><input id="fq" class="txt" type="search" placeholder="N° de PV, série, type…" value="${esc(F.q)}"></div>`;
    if (type === 'chips') {
      const vals = valeursUniques(rows, k, opt).sort((a, b) => ORDRE(a) - ORDRE(b) || a.localeCompare(b, 'fr', { numeric: true }));
      const on = F.chips[k] || [];
      return `<div class="f"><span class="lab">${esc(lib)}</span><div class="chips">${vals.map(v => `<button type="button" class="chip" data-chip="${esc(k)}" data-v="${esc(v)}" aria-pressed="${on.includes(v)}">${esc(v)}</button>`).join('')}</div></div>`;
    }
    if (type === 'select') return `<div class="f"><label>${esc(lib)}<select class="sel" data-sel="${esc(k)}"><option value="">— Toutes —</option>${valeursUniques(rows, k).map(v => `<option${F.sel[k] === v ? ' selected' : ''}>${esc(v)}</option>`).join('')}</select></label></div>`;
    if (type === 'min') return `<div class="f"><label>${esc(lib)}<select class="sel" data-min="${esc(k)}"><option value="">— Indifférent —</option>${opt.map(v => `<option value="${nombre(v)}"${String(F.min[k] ?? '') === String(nombre(v)) ? ' selected' : ''}>${esc(v)} ou mieux</option>`).join('')}</select></label></div>`;
    if (type === 'nummin') return `<div class="f"><label>${esc(lib)}<input class="txt" type="number" data-nummin="${esc(k)}" placeholder="ex. 40" value="${esc(F.nummin[k] ?? '')}"></label></div>`;
    if (type === 'corpus') return `<label class="case"><input type="checkbox" id="fcorpus"${F.corpus ? ' checked' : ''}> Document retrouvé dans le corpus PDF</label>`;
    if (type === 'cumul') return ['feu', 'rc', 'fb'].filter(o => o !== etat.cat).map(o => {
      const vals = trierClasses(rows.flatMap(r => r.cumul?.[o] || []));
      if (!vals.length) return '';
      const on = F.cumul[o] || [];
      return `<div class="f"><span class="lab">Cumul ${esc(SECU_LIB[o].toLowerCase())}</span><div class="sub">Fiches combinables avec une fiche ${esc(SECU_LIB[o].toLowerCase())} de cette classe (ForsterData).</div>
        <div class="chips">${vals.map(v => `<button type="button" class="chip" data-cumul="${o}" data-v="${esc(v)}" aria-pressed="${on.includes(v)}">${esc(v)}</button>`).join('')}</div></div>`;
    }).join('');
    return '';
  }).join('');
  const maj = () => { etat.page = 1; run(); };
  const fq = $('#fq'); if (fq) fq.oninput = () => { F.q = fq.value; clearTimeout(fq._t); fq._t = setTimeout(maj, 200); };
  hote.querySelectorAll('[data-chip]').forEach(b => b.onclick = () => {
    const a = (F.chips[b.dataset.chip] ||= []), i = a.indexOf(b.dataset.v); i >= 0 ? a.splice(i, 1) : a.push(b.dataset.v);
    b.setAttribute('aria-pressed', i < 0); maj();
  });
  hote.querySelectorAll('[data-cumul]').forEach(b => b.onclick = () => {
    const a = (F.cumul[b.dataset.cumul] ||= []), i = a.indexOf(b.dataset.v); i >= 0 ? a.splice(i, 1) : a.push(b.dataset.v);
    b.setAttribute('aria-pressed', i < 0); maj();
  });
  hote.querySelectorAll('[data-sel]').forEach(s => s.onchange = () => { F.sel[s.dataset.sel] = s.value; maj(); });
  hote.querySelectorAll('[data-min]').forEach(s => s.onchange = () => { F.min[s.dataset.min] = s.value; maj(); });
  hote.querySelectorAll('[data-nummin]').forEach(s => s.oninput = () => { F.nummin[s.dataset.nummin] = s.value; maj(); });
  const fc = $('#fcorpus'); if (fc) fc.onchange = () => { F.corpus = fc.checked; maj(); };
}
function filtrerCat(rows) {
  const F = etat.F, t = normTxt(F.q).replace(/\s/g, '');
  return rows.filter(r => {
    if (t && !normTxt([r.numero_pv, r.numero_normalise, r.serie, r.type_chassis, r.objet, r.systemes, r.perfs].join(' ')).replace(/\s/g, '').includes(t)) return false;
    for (const [k, vals] of Object.entries(F.chips)) if (vals.length && !vals.some(v => String(r[k] ?? '').split(',').includes(v))) return false;
    for (const [k, v] of Object.entries(F.sel)) if (v && r[k] !== v) return false;
    for (const [o, vals] of Object.entries(F.cumul)) if (vals.length && !vals.some(v => r.cumul?.[o]?.includes(v))) return false;
    for (const [k, v] of Object.entries(F.min)) if (v !== '' && v != null && !((nombre(r[k]) ?? -1) >= +v)) return false;
    for (const [k, v] of Object.entries(F.nummin)) if (v !== '' && v != null && !((r[k] ?? -999) >= +v)) return false;
    if (F.corpus && !r.document_pv_id) return false;
    return true;
  });
}

/* ---------- Tableau, tri, pagination ---------- */
function trier(rows) {
  if (!etat.tri) return rows;
  const { k, d } = etat.tri;
  return [...rows].sort((a, b) => {
    const x = a[k], y = b[k];
    if (x == null || x === '') return 1; if (y == null || y === '') return -1;
    return (typeof x === 'number' && typeof y === 'number' ? x - y : String(x).localeCompare(String(y), 'fr', { numeric: true })) * d;
  });
}
function pager(total) {
  const pages = Math.max(1, Math.ceil(total / PAGE)), p = Math.min(etat.page, pages);
  etat.page = p;
  if (pages === 1) return '';
  const set = [...new Set([1, pages, p - 1, p, p + 1].filter(n => n >= 1 && n <= pages))].sort((a, b) => a - b);
  let dernier = 0, h = `<button data-page="${p - 1}"${p === 1 ? ' disabled' : ''}>Précédent</button>`;
  for (const n of set) { if (n - dernier > 1) h += '<span>…</span>'; h += `<button data-page="${n}" aria-current="${n === p}">${n}</button>`; dernier = n; }
  return h + `<button data-page="${p + 1}"${p === pages ? ' disabled' : ''}>Suivant</button>`;
}
function tableau(cols, rows, cellule) {
  const tete = cols.map(([k, l]) => {
    const fl = etat.tri && etat.tri.k === k ? (etat.tri.d > 0 ? '▲' : '▼') : '';
    return `<th class="triable" data-tri="${esc(k)}">${esc(l)}<span class="fl">${fl}</span></th>`;
  }).join('');
  return `<div class="defile"><table class="liste"><thead><tr><th class="cb" title="Comparer"></th>${tete}</tr></thead><tbody>${rows.map(r =>
    `<tr data-id="${esc(r.id)}" tabindex="0"><td class="cb"><input type="checkbox" aria-label="Comparer" data-cmp="${esc(r.id)}"${etat.cmp.has(r.id) ? ' checked' : ''}></td>${cols.map(c => cellule(r, c)).join('')}</tr>`).join('')}</tbody></table></div>`;
}
function brancherTableau(rows) {
  const zone = $('#resultats');
  zone.querySelectorAll('th[data-tri]').forEach(th => th.onclick = () => {
    const k = th.dataset.tri;
    etat.tri = etat.tri && etat.tri.k === k ? (etat.tri.d > 0 ? { k, d: -1 } : null) : { k, d: 1 };
    run();
  });
  zone.querySelectorAll('[data-cmp]').forEach(cb => cb.onchange = () => {
    const r = rows.find(x => String(x.id) === cb.dataset.cmp);
    if (cb.checked) { if (etat.cmp.size >= 4) { cb.checked = false; alert('4 éléments maximum à comparer.'); return; } etat.cmp.set(r.id, r); } else etat.cmp.delete(r.id);
    barreComparaison();
  });
  $('#pager').querySelectorAll('[data-page]').forEach(b => b.onclick = () => { etat.page = +b.dataset.page; run(); $('.resultats').scrollIntoView({ block: 'start', behavior: 'smooth' }); });
}

/* ---------- Rendu principal ---------- */
function run() {
  const cat = etat.cat;
  $('#titre-cat').textContent = CATS[cat].label;
  if (cat === 'feu') return runFeu();
  const s = {};
  versHash(s);
  $('#actifs').innerHTML = '';
  $('#legende').innerHTML = cat === 'rapports'
    ? "Rapports d'essais du dossier « Rapports d'essais » : extraction automatique, classes à vérifier sur l'original. Un rapport ne vaut pas classement au feu."
    : `Fiches de la base ForsterData. Colonne Corpus : <b>✓</b> PV/rapport retrouvé dans le corpus PDF · <b>≈</b> rapprochement partiel · <b>⚠</b> classe différente de celle lue dans le document · <b>—</b> non retrouvé.`;
  const tous = donnees(cat), rows = trier(filtrerCat(tous));
  lignes = rows;
  $('#compte').textContent = `${rows.length}${rows.length !== tous.length ? ' sur ' + tous.length : ''} ${cat === 'rapports' ? 'rapport(s)' : 'fiche(s)'}`;
  const pg = pager(rows.length);
  const tranche = rows.slice((etat.page - 1) * PAGE, etat.page * PAGE);
  if (!rows.length) { $('#resultats').innerHTML = '<div class="vide-res">Aucun résultat. Retirez un filtre.</div>'; $('#pager').innerHTML = ''; return; }
  $('#resultats').innerHTML = tableau(COLS[cat], tranche, (r, [k, , fort]) => {
    let v = r[k];
    if (k === 'perfs') return `<td>${autres(v)}</td>`;
    if (k === 'classe') return `<td><span class="classe ${cat === 'feu' ? '' : 'autre'}">${esc(v || '—')}</span></td>`;
    if (k === 'cumul_txt') return `<td class="masque-sm">${v ? autres(v.replace(/ · /g, ',').replace(/ /g, ',')) : '—'}</td>`;
    if (k === 'doc_etat') return `<td class="etat-doc ${v === '⚠ écart' ? 'ecart' : ''}" title="${esc(r.doc_num || 'non retrouvé dans le corpus')}">${esc(v)}</td>`;
    if (k === 'numero_pv') v = String(v || '').split('\n')[0];
    if (k === 'date_emission') return `<td class="nowrap">${esc(v || '—')}</td>`;
    return `<td class="${fort ? 'fort' : ''}">${esc(v == null || v === '' ? '—' : v)}</td>`;
  });
  $('#pager').innerHTML = pg;
  brancherTableau(rows);
}

function runFeu() {
  const s = lireEtat();
  versHash(s);
  majFacettes(s);
  puceActives(s);
  $('#legende').innerHTML = `Classe <span class="classe">EI 60</span> lue dans le PV · <span class="classe fichier">EI 60</span> reprise du nom de fichier · <span class="classe autre">RC3</span> cumul déclaré dans ForsterData (même série, même type d'ouvrage) — les classes incluent celles des extensions rattachées.`;
  const { sql, params } = buildQuery(s, $('#tri').value);
  $('#sql').textContent = sql + '\n\n-- paramètres : ' + JSON.stringify(params);
  const tous = q(sql, params);
  tous.forEach(r => { r.validite_tri = r.validite; });
  lignes = trier(tous);
  $('#compte').textContent = `${lignes.length} PV`;
  if (!lignes.length) {
    $('#pager').innerHTML = '';
    $('#resultats').innerHTML = `<div class="vide-res">Aucun PV ne correspond. Retirez un filtre (puces ci-dessus)${s.largeur || s.hauteur ? ', ou cochez « Inclure les PV où cette dimension n\'a pas été extraite »' : ''}.</div>`;
    return;
  }
  const pg = pager(lignes.length);
  const tranche = lignes.slice((etat.page - 1) * PAGE, etat.page * PAGE);
  const cols = [['numero_normalise', 'PV', 1], ['classements', 'Classes'], ['typologies', 'Application'], ['systemes', 'Série'], ['verrier', 'Verrier'], ['cumul_fd', 'Cumul RC / FB'], ['validite', 'Validité']];
  $('#resultats').innerHTML = tableau(cols, tranche, (r, [k]) => {
    if (k === 'numero_normalise') {
      let t = '';
      if (s.reference) {
        const h = hitsQuery(r.id, s.reference), hits = q(h.sql, h.params);
        if (hits.length) t = `<div class="trouve">${hits.map(x => `<b>${esc(x.ref)}</b> — ${esc(x.doc)}${x.planche ? ', ' + esc(x.planche) : x.page ? ', p. ' + esc(x.page) : ''}`).join(' · ')}</div>`;
      }
      if ((s.largeur || s.hauteur) && s.dim_inconnue) { const d = dimInconnueQuery(r.id, s.objet_dim); if (!q(d.sql, d.params)[0].n) t += '<div class="trouve">Dimension non renseignée : à vérifier.</div>'; }
      return `<td class="fort">${esc(r.numero_normalise)}${r.auto ? ' <span class="badge auto" title="Extraction automatique — à vérifier">auto</span>' : ''}<div class="objet-court">${esc((r.objet || '').slice(0, 110))}</div>${t}</td>`;
    }
    if (k === 'classements') return `<td>${classes(r.classements)}</td>`;
    if (k === 'cumul_fd') return `<td class="masque-sm">${r.cumul_fd ? autres(r.cumul_fd) : '—'}</td>`;
    if (k === 'validite') return `<td class="masque-sm">${validite(r.validite)}</td>`;
    if (k === 'verrier') return `<td class="masque-sm">${esc(LIBELLES_VERRIER[r.verrier] || r.verrier || '—')}</td>`;
    if (k === 'systemes') return `<td>${esc((r.systemes || '—').replace(/,/g, ', '))}</td>`;
    return `<td>${esc((r[k] || '—').replace(/,/g, ', '))}</td>`;
  });
  $('#pager').innerHTML = pg;
  brancherTableau(lignes);
}

/* ---------- Tiroir : fiche ForsterData ---------- */
const DIMS = [['largeur_verre_mm', 'Largeur verre maxi'], ['hauteur_verre_mm', 'Hauteur verre maxi'], ['largeur_1v_mm', 'Largeur BP 1 vantail'], ['largeur_2v_mm', 'Largeur BP 2 vantaux'],
  ['hauteur_bp1v_mm', 'Hauteur BP 1 vantail'], ['hauteur_bp2v_mm', 'Hauteur BP 2 vantaux'], ['hauteur_cloison_mm', 'Hauteur cloison maxi']];
const CHAMPS_ENTETE = new Set(['Type de châssis', 'Série', 'Classe', 'Degré feu', 'n° PV', 'Validité', 'Verrier', 'Largeur Verre', 'Hauteur Verre', 'Largeur 1V', 'Largeur 2V',
  'Hauteur BP1V', 'Hauteur BP2V', 'Hauteur Cloison', 'A', 'E', 'V', 'V type abc', 'Rw', 'Rw C', 'Rw Ctr', 'Type de résistance']);
const vide_ = v => v == null || v === '' || v === '-' || v === '—';

function ouvrirFiche(id) {
  const f = q(`SELECT f.*, d.numero_normalise AS doc_num, d.type_code AS doc_type FROM fiche_forsterdata f LEFT JOIN document d ON d.id = f.document_pv_id WHERE f.id = :id`, { ':id': id })[0];
  if (!f) return;
  const det = JSON.parse(f.details_json);
  const titre = `Forster ${f.serie || ''} ${f.type_chassis} ${f.classe || ''}`;
  const liens = q(`SELECT o.id, o.categorie, o.classe, o.type_chassis, o.serie, o.numero_pv, l.motif FROM lien_forsterdata l
      JOIN fiche_forsterdata o ON o.id = CASE WHEN l.fiche_a = :id THEN l.fiche_b ELSE l.fiche_a END WHERE :id IN (l.fiche_a, l.fiche_b)`, { ':id': id });
  const blocLiens = ['feu', 'rc', 'fb'].includes(f.categorie) ? `<div class="kv liens"><h4>Performances cumulées</h4><div class="sub">Fiches de même série et même type d'ouvrage déclarées combinables (« Cumul de perf »). Le cumul vaut pour la construction décrite dans les deux documents.</div>
    ${['feu', 'rc', 'fb'].filter(c => c !== f.categorie).map(c => {
      const l = liens.filter(x => x.categorie === c).sort((a, b) => ORDRE(a.classe) - ORDRE(b.classe));
      return `<div class="lkg"><div class="lkh">${SECU_LIB[c]}</div>${l.length ? l.map(x => `<button type="button" class="lk" data-fiche="${esc(x.id)}"><b>${esc(x.classe)}</b><span>${esc(x.type_chassis)} ${esc(x.serie)}</span><em>${esc(String(x.numero_pv || '').split('\n')[0])}</em></button>`).join('') : '<div class="none">Aucune fiche liée</div>'}</div>`;
    }).join('')}</div>` : '';
  const ctrl = q(`SELECT description FROM controle_humain WHERE ligne_id = :id AND statut = 'ouvert'`, { ':id': id });
  const blocDoc = f.document_pv_id ? `<div class="kv"><h4>Document du corpus</h4><p>${esc(f.doc_num)} <span class="note">(${esc(f.doc_type)}, rapprochement ${esc(f.rapprochement)})</span>
      <button type="button" class="btn" data-doc="${esc(f.document_pv_id)}">Ouvrir la fiche du document</button></p>
      ${ctrl.map(c => `<div class="ancre-avert">${esc(c.description)}</div>`).join('')}</div>` : `<div class="kv"><h4>Document du corpus</h4><p class="none">PV / rapport « ${esc(String(f.numero_pv || '—').split('\n')[0])} » non retrouvé dans les PDF du corpus.</p></div>`;
  const dims = DIMS.filter(([k]) => f[k]);
  const nums = f.categorie === 'aev' ? [['A', f.classe_air], ['E', f.classe_eau], ['V', f.classe_vent]] : f.categorie === 'acoustique' ? [['Rw (dB)', f.rw_db], ['C', f.c_db], ['Ctr', f.ctr_db]] : [];
  const champs = Object.entries(det).filter(([k, v]) => !CHAMPS_ENTETE.has(k) && !vide_(v));
  ouvrirTiroir(`<div class="dh"><button class="x" type="button" aria-label="Fermer">×</button><h3>${esc(titre)}</h3>
      <div class="meta">${f.verrier ? `<div class="vv">${esc(f.verrier)}</div>` : ''}<div class="pv">${esc(String(f.numero_pv || '—').replace(/\n/g, ' · '))}</div>
      ${f.categorie === 'feu' ? validite(f.validite) : ''}<span class="badge b-na">Fiche ForsterData ${esc(f.id)}</span></div>
      <div class="actions"><button type="button" class="btn" id="dcmp">${etat.cmp.has(f.id) ? 'Retirer de la comparaison' : 'Ajouter à la comparaison'}</button><button type="button" class="btn" id="dcopie">Copier le n° de PV</button></div></div>
    <div class="db">${blocLiens}${blocDoc}
      ${nums.length ? `<div class="kv nums">${nums.filter(([, v]) => v != null).map(([k, v]) => `<div><span>${esc(k)}</span><b>${esc(v)}</b></div>`).join('')}</div>` : ''}
      ${dims.length ? `<div class="kv"><h4>Dimensions maximales (mm)</h4><div class="nums">${dims.map(([k, l]) => `<div><span>${esc(l)}</span><b>${Number(f[k]).toLocaleString('fr-FR')}</b></div>`).join('')}</div></div>` : ''}
      ${champs.map(([k, v]) => `<div class="kv"><h4>${esc(k)}</h4><div class="v">${esc(v)}</div></div>`).join('')}</div>`);
  const d = $('#detail');
  d.querySelectorAll('[data-fiche]').forEach(b => b.onclick = () => ouvrirFiche(b.dataset.fiche));
  d.querySelectorAll('[data-doc]').forEach(b => b.onclick = () => detail(b.dataset.doc));
  $('#dcopie').onclick = () => navigator.clipboard?.writeText(String(f.numero_pv || '').split('\n')[0]);
  $('#dcmp').onclick = () => {
    if (etat.cmp.has(f.id)) etat.cmp.delete(f.id);
    else if (etat.cmp.size < 4 && etat.cat === f.categorie) etat.cmp.set(f.id, (DONNEES[f.categorie] || []).find(x => x.id === f.id) || f);
    barreComparaison(); ouvrirFiche(id); run();
  };
}
function ouvrirTiroir(html) {
  const el = $('#detail');
  el.innerHTML = html; el.hidden = false; $('#voile').hidden = false;
  el.querySelectorAll('.x, .fermer').forEach(b => b.onclick = fermer);
  el.scrollTop = 0;
}
function fermer() { $('#detail').hidden = true; $('#voile').hidden = true; $('#modal').hidden = true; }

/* ---------- Comparaison (2 à 4 éléments) ---------- */
function barreComparaison() {
  const n = etat.cmp.size;
  $('#cmpbar').innerHTML = n ? `<div class="cmpbar"><span>${n} élément(s) sélectionné(s)</span><button type="button" class="go"${n < 2 ? ' disabled' : ''}>Comparer</button><button type="button" class="clr">Vider</button></div>` : '';
  if (!n) return;
  $('#cmpbar .go').onclick = comparer;
  $('#cmpbar .clr').onclick = () => { etat.cmp.clear(); barreComparaison(); run(); };
}
function champsComparaison(r) {
  if (etat.cat === 'feu') return { _titre: r.numero_normalise, 'PV': r.numero_normalise, 'Objet': r.objet, 'Classes': (r.classements || '').replace(/\*/g, ' (nom de fichier)').replace(/,/g, ', '), 'Application': r.typologies,
    'Série': r.systemes, 'Verrier': LIBELLES_VERRIER[r.verrier] || r.verrier, 'Cumul RC / FB (ForsterData)': r.cumul_fd, 'Rapports même système / typologie': r.complements,
    'Validité': r.validite, 'Dernière reconduction': r.derniere_reconduction, 'Extensions': r.nb_extensions, 'Points à vérifier': r.nb_controles, 'Fichier': r.nom_fichier };
  if (etat.cat === 'rapports') return { _titre: r.numero_normalise, 'N°': r.numero_normalise, 'Objet': r.objet, 'Domaine': r.domaine_lib, 'Classes': r.perfs, 'Système': r.systemes, 'Typologie': r.typologie,
    'Laboratoire': r.laboratoire, 'Date': r.date_emission, 'Type': r.type_lib, 'Cumuls énoncés': r.nb_cumuls };
  const o = { _titre: `${r.classe || ''} — ${r.serie || ''} ${r.type_chassis || ''}`, 'Classe': r.classe, 'Corpus': r.doc_num ? `${r.doc_num} (${r.rapprochement})` : 'non retrouvé', 'Cumul': r.cumul_txt };
  for (const [k, v] of Object.entries(JSON.parse(r.details_json || '{}'))) if (!vide_(v)) o[k] = v;
  return o;
}
function comparer() {
  const items = [...etat.cmp.values()].map(champsComparaison);
  const cles = [...new Set(items.flatMap(Object.keys))].filter(k => k !== '_titre');
  const m = $('#modal');
  const rendre = diff => {
    const ks = diff ? cles.filter(k => new Set(items.map(i => String(i[k] ?? ''))).size > 1) : cles;
    m.querySelector('.mb').innerHTML = `<table class="cmp"><thead><tr><th class="k"></th>${items.map((it, i) => `<th>${esc(it._titre || 'Élément ' + (i + 1))}</th>`).join('')}</tr></thead>
      <tbody>${ks.map(k => `<tr><th class="k">${esc(k)}</th>${items.map(it => `<td>${esc(it[k] ?? '—')}</td>`).join('')}</tr>`).join('')}</tbody></table>`;
  };
  m.innerHTML = `<div class="mh"><h3>Comparaison — ${esc(CATS[etat.cat].label)}</h3><label><input type="checkbox" id="diff"> Uniquement les différences</label><button type="button" class="btn" id="mclose">Fermer</button></div><div class="mb"></div>`;
  m.hidden = false; $('#voile').hidden = false;
  rendre(false);
  $('#diff').onchange = e => rendre(e.target.checked);
  $('#mclose').onclick = fermer;
}

function exporterCSV() {
  const cols = etat.cat === 'feu'
    ? ['numero_normalise', 'classements', 'typologies', 'systemes', 'verrier', 'cumul_fd', 'complements', 'validite', 'derniere_reconduction', 'nb_extensions', 'auto', 'objet', 'nom_fichier']
    : COLS[etat.cat].map(c => c[0]).concat(etat.cat === 'rapports' ? ['objet', 'type_lib'] : ['id', 'verrier', 'doc_num', 'rapprochement', 'cumul_perf']);
  const csv = [cols.join(';'), ...lignes.map(r => cols.map(c => `"${String(r[c] ?? '').replace(/"/g, '""')}"`).join(';'))];
  const a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob(['﻿' + csv.join('\n')], { type: 'text/csv;charset=utf-8' }));
  a.download = `forster-${etat.cat}.csv`; a.click();
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
      ${pv.fichier_source_id && pv.fichier_source_id.startsWith('FIC-RAP') ? `<div class="ancre-avert">Rapport d'essais extrait automatiquement (${esc(pv.type_code)}) : classes et métadonnées à vérifier sur l'original. Ce document ne vaut pas classement au feu.</div>` : ''}
      ${pv.fichier_source_id && pv.fichier_source_id.startsWith('FIC-AUTO') ? '<div class="ancre-avert">Ce PV provient de l\'extraction automatique (OCR) : toutes les données sont à vérifier sur l\'original.</div>' : ''}
      <p><b>${esc(pv.objet || '')}</b></p>
      <p class="note">Fichier : ${esc(pv.nom_fichier || '—')}${pv.url ? ` · <a href="${esc(pv.url)}" target="_blank" rel="noopener">ouvrir le PDF</a>` : ''}</p>
      ${(() => { const fd = q(`SELECT DISTINCT o.id, o.categorie, o.classe, o.type_chassis, o.serie, o.numero_pv FROM rat r2 JOIN fiche_forsterdata fa ON fa.document_pv_id = r2.document_id
          JOIN lien_forsterdata l ON fa.id IN (l.fiche_a, l.fiche_b) JOIN fiche_forsterdata o ON o.id = CASE WHEN l.fiche_a = fa.id THEN l.fiche_b ELSE l.fiche_a END
          WHERE r2.pv_principal_id = :id AND o.categorie IN ('feu','rc','fb') ORDER BY o.categorie, o.classe`, p);
        const fiches = q(`SELECT DISTINCT fa.id, fa.categorie, fa.classe, fa.type_chassis, fa.serie FROM rat r2 JOIN fiche_forsterdata fa ON fa.document_pv_id = r2.document_id WHERE r2.pv_principal_id = :id`, p);
        if (!fiches.length) return '';
        return `<div class="kv liens"><h4>Performances cumulées (ForsterData)</h4><div class="sub">Fiche(s) ForsterData de ce document : ${fiches.map(x => `<button type="button" class="lien-fiche" data-fiche="${esc(x.id)}">${esc(x.serie)} ${esc(x.type_chassis)} ${esc(x.classe || '')}</button>`).join(' · ')}</div>
          ${fd.length ? fd.map(x => `<button type="button" class="lk" data-fiche="${esc(x.id)}"><b>${esc(x.classe)}</b><span>${esc(SECU_LIB[x.categorie])} — ${esc(x.type_chassis)} ${esc(x.serie)}</span><em>${esc(String(x.numero_pv || '').split('\n')[0])}</em></button>`).join('') : '<div class="none">Aucun cumul déclaré dans ForsterData.</div>'}</div>`; })()}
      <h3>Classements feu</h3>${table(q(`SELECT numero_normalise AS document, configuration, classe_normalisee AS classe, sens_feu, condition_texte AS condition, page_doc AS page, statut_extraction AS _statut FROM v_classement_feu WHERE document_id IN (${docs})`, p))}
      ${q(`SELECT count(*) n FROM performance WHERE document_id IN (${docs}) AND domaine_code <> 'feu'`, p)[0].n ? `<h3>Autres performances</h3>${table(q(`SELECT v.numero_normalise AS document, d.libelle AS domaine, v.classe_normalisee AS classe,
          v.libelle_tel_qu_ecrit AS "tel qu'écrit", v.condition_texte AS condition, v.page_doc AS page, v.statut_extraction AS _statut
          FROM v_performance_multi v JOIN ref_domaine_performance d ON d.code = v.domaine_code WHERE v.document_id IN (${docs}) AND v.domaine_code <> 'feu'`, p))}` : ''}
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
    'Cumuls': () => {
      const enonces = q(`SELECT d.numero_normalise AS "énoncé par", s.nom AS "système", t.libelle AS typologie, da.libelle || ' ' || cp.classe_a AS "performance A",
          db.libelle || ' ' || cp.classe_b AS "performance B", cp.statut_cumul AS statut, cp.condition_texte AS condition, cp.justificatifs AS justificatifs, sp.page_doc AS page
        FROM cumul_performance cp JOIN document d ON d.id = cp.document_id LEFT JOIN systeme s ON s.id = cp.systeme_id LEFT JOIN ref_typologie t ON t.code = cp.typologie_code
        JOIN ref_domaine_performance da ON da.code = cp.domaine_a JOIN ref_domaine_performance db ON db.code = cp.domaine_b LEFT JOIN source_page sp ON sp.id = cp.source_page_id
        WHERE cp.document_id IN (${docs}) OR EXISTS (SELECT 1 FROM cfg WHERE cfg.pv_principal_id = :id
          AND cfg.sysgrp = CASE WHEN cp.systeme_id LIKE 'SYS-FUEGO-LIGHT%' THEN 'SYS-FUEGO-LIGHT' ELSE cp.systeme_id END
          AND cfg.famille = CASE WHEN cp.typologie_code IN ('chassis_fixe','cloison_vitree','cloison_vitree_bord_a_bord') THEN 'fixe' ELSE cp.typologie_code END)
        ORDER BY cp.domaine_b, cp.classe_b`, p);
      const potentiels = q(`SELECT DISTINCT dm.libelle AS domaine, pa.classe_normalisee AS classe, d.numero_normalise AS rapport, d.type_code AS type, d.date_emission AS date, o.nom AS laboratoire
        FROM cfg JOIN pa ON pa.sysgrp = cfg.sysgrp AND pa.famille = cfg.famille JOIN document d ON d.id = pa.document_id
        JOIN ref_domaine_performance dm ON dm.code = pa.domaine_code LEFT JOIN organisme o ON o.id = d.laboratoire_id
        WHERE cfg.pv_principal_id = :id ORDER BY dm.libelle, pa.classe_normalisee`, p);
      return `<div class="ancre-avert">Un cumul n'est valable que si la même construction (vitrage, serrure, quincaillerie, dimensions) est couverte par le PV feu et par le rapport de l'autre domaine. Les lignes « sous réserve » renvoient à un PV ou à un avis de chantier.</div>
        <h3>Cumuls énoncés dans les documents</h3>${table(enonces)}
        <h3>Rapports d'essais du même système et de la même typologie (rapprochement, non certifié)</h3>${table(potentiels)}`;
    },
    'À vérifier': () => table(q(`SELECT d.numero_normalise AS document, t.libelle AS type, ch.description FROM controle_humain ch JOIN document d ON d.id = ch.document_id
          JOIN ref_type_controle t ON t.code = ch.type_code WHERE ch.document_id IN (${docs}) AND ch.statut = 'ouvert'`, p)),
  };
  const nb = {
    'Composants': q(`SELECT count(*) n FROM document_composant WHERE document_id IN (${docs}) AND parent_id IS NULL`, p)[0].n,
    'Dimensions': q(`SELECT count(*) n FROM dimension_format WHERE document_id IN (${docs})`, p)[0].n,
    'À vérifier': q(`SELECT count(*) n FROM controle_humain WHERE document_id IN (${docs}) AND statut = 'ouvert'`, p)[0].n,
    'Cumuls': q(`SELECT count(*) n FROM cumul_performance cp WHERE cp.document_id IN (${docs}) OR EXISTS (SELECT 1 FROM cfg WHERE cfg.pv_principal_id = :id
          AND cfg.sysgrp = CASE WHEN cp.systeme_id LIKE 'SYS-FUEGO-LIGHT%' THEN 'SYS-FUEGO-LIGHT' ELSE cp.systeme_id END
          AND cfg.famille = CASE WHEN cp.typologie_code IN ('chassis_fixe','cloison_vitree','cloison_vitree_bord_a_bord') THEN 'fixe' ELSE cp.typologie_code END)`, p)[0].n,
  };
  ouvrirTiroir(`<div class="detail-tete"><h2>${esc(pv.numero_normalise)}</h2>${pv.fichier_source_id && (pv.fichier_source_id.startsWith('FIC-AUTO') || pv.fichier_source_id.startsWith('FIC-RAP')) ? '<span class="badge auto">à vérifier</span>' : '<span class="badge relu">saisie relue</span>'}
      <button class="fermer" type="button">Fermer</button></div>
    <div class="onglets" role="tablist">${Object.keys(ong).map((k, i) => `<button role="tab" aria-selected="${i === 0}" data-o="${esc(k)}">${esc(k)}${nb[k] != null ? ` <small>${nb[k]}</small>` : ''}</button>`).join('')}</div>
    <div class="contenu" id="contenu"></div>`);
  const el = $('#detail');
  const montrer = k => {
    $$('.onglets button').forEach(b => b.setAttribute('aria-selected', b.dataset.o === k));
    $('#contenu').innerHTML = ong[k]();
    $$('#contenu [data-fiche]').forEach(b => b.onclick = () => ouvrirFiche(b.dataset.fiche));
    const fc = $('#filtre-comp');
    if (fc) fc.oninput = () => { const t = fc.value.toLowerCase(); $$('#liste-comp tbody tr').forEach(tr => { tr.hidden = t && !tr.textContent.toLowerCase().includes(t); }); };
  };
  el.querySelector('.onglets').onclick = e => { const b = e.target.closest('button'); if (b) montrer(b.dataset.o); };
  montrer('Synthèse');
}

function vueCumuls() {
  const rows = q(`SELECT d.numero_normalise AS "énoncé par", d.type_code AS type, s.nom AS "système", t.libelle AS typologie,
      cp.domaine_a || ' ' || cp.classe_a AS "performance A", cp.domaine_b || ' ' || cp.classe_b AS "performance B",
      cp.statut_cumul AS statut, cp.condition_texte AS condition, cp.justificatifs, sp.page_doc AS page, cp.statut_extraction AS _statut
    FROM cumul_performance cp JOIN document d ON d.id = cp.document_id LEFT JOIN systeme s ON s.id = cp.systeme_id
    LEFT JOIN ref_typologie t ON t.code = cp.typologie_code LEFT JOIN source_page sp ON sp.id = cp.source_page_id
    ORDER BY CASE cp.statut_cumul WHEN 'declare_fabricant' THEN 0 WHEN 'sous_reserve' THEN 1 ELSE 2 END, s.nom, t.libelle, cp.domaine_b, cp.classe_b`);
  ouvrirTiroir(`<div class="detail-tete"><h2>Cumuls de performances</h2><button class="fermer" type="button">Fermer</button></div>
    <div class="contenu"><div class="ancre-avert">Cumuls <b>énoncés</b> par un document : synthèse Forster (« declare_fabricant », « sous_reserve » = sous PV ou avis de chantier) ou rapport d'essai (« constate_rapport » : les deux classes figurent dans le même rapport, ou l'éprouvette est décrite comme coupe-feu dans le nom du rapport). Les cumuls ForsterData (« declare_fabricant ») suivent la règle : même série, même type d'ouvrage, déclaration dans « Cumul de perf ». Aucun PV de classement feu du corpus ne prononce lui-même de classe d'effraction, pare-balles ou acoustique.</div>
    <label class="champ" style="max-width:320px">Filtrer<input type="search" id="filtre-cumul" placeholder="Unico, RC3, FB4, sous_reserve…"></label>
    <div id="liste-cumul">${table(rows)}</div></div>`);
  const f = $('#filtre-cumul');
  f.oninput = () => { const t = f.value.toLowerCase(); $$('#liste-cumul tbody tr').forEach(tr => { tr.hidden = t && !tr.textContent.toLowerCase().includes(t); }); };
}


/* ---------- Initialisation ---------- */
async function init() {
  try {
    const { db, meta } = await openDatabase(m => { $('#statut').textContent = m; });
    DB = db;
    DB.exec(PREPARATION);
    for (const c of Object.keys(CATS)) CATS[c].n = compteCat(c);
    $('#statut').textContent = `${CATS.feu.n} PV · ${CATS.rapports.n} rapports · ${CATS.rc.n + CATS.fb.n + CATS.aev.n + CATS.acoustique.n} fiches ForsterData · base du ${String(meta.genere_le).slice(0, 10)}`;
    const videF = { systeme: [], typologie: [], verrier: [], support: [], type_vitrage: [], complement: [], domaine: [], cumul_fd: [], etat: '' };
    for (const nom of FACETTES) {
      const { sql, params } = facetQuery(nom, videF);
      libelles[nom] = Object.fromEntries(q(sql, params).map(r => [r.code, nom === 'verrier' ? (LIBELLES_VERRIER[r.code] || r.code) : r.libelle]));
    }
    libelles.complement = Object.fromEntries(Object.entries(COMPLEMENTS).filter(([c]) => libelles.complement[c] !== undefined));
    libelles.cumul_fd = Object.fromEntries(trierClasses(Object.keys(libelles.cumul_fd)).map(c => [c, c]));
    $('[name=fonction]').insertAdjacentHTML('beforeend', q('SELECT code FROM ref_fonction_serrure').map(r => `<option>${esc(r.code)}</option>`).join(''));
    $('#liste-refs').innerHTML = q(`SELECT rc.reference_normalisee AS r, coalesce(o.nom,'') AS f FROM reference_composant rc LEFT JOIN organisme o ON o.id = rc.fabricant_id
        WHERE rc.id IN (SELECT reference_id FROM document_composant) ORDER BY 1 LIMIT 3000`).map(x => `<option value="${esc(x.r)}">${esc(x.f)}</option>`).join('');
    const initial = depuisHash();
    majFacettes(initial);
    ecrireEtat(initial);
    rendreGroupes(); rendreFiltresCat();
    $('#groupes').onclick = e => { const b = e.target.closest('.cat'); if (b) choisirCat(b.dataset.cat); };
    let minuterie;
    $('#filtres').addEventListener('input', e => { etat.page = 1; clearTimeout(minuterie); minuterie = setTimeout(run, e.target.type === 'search' || e.target.type === 'number' ? 250 : 0); });
    $('#tri').addEventListener('change', () => { etat.tri = null; run(); });
    $('#reinit').onclick = () => {
      if (etat.cat === 'feu') ecrireEtat({ ...DEFAUTS, systeme: [], typologie: [], verrier: [], support: [], type_vitrage: [], complement: [], domaine: [], cumul_fd: [] });
      else { etat.F = vide(); rendreFiltresCat(); }
      etat.page = 1; run();
    };
    $('#voir-cumuls').onclick = vueCumuls;
    $('#actifs').onclick = e => {
      const b = e.target.closest('button'); if (!b) return;
      const s = lireEtat(); const k = b.dataset.k;
      if (MULTI.includes(k)) s[k] = s[k].filter(x => x !== b.dataset.v); else s[k] = DEFAUTS[k] ?? '';
      ecrireEtat(s); run();
    };
    const ouvrir = tr => { if (!tr) return; const id = tr.dataset.id; if (etat.cat === 'feu' || etat.cat === 'rapports') detail(id); else ouvrirFiche(id); };
    $('#resultats').addEventListener('click', e => { if (e.target.matches('input[type=checkbox]') || e.target.closest('.trouve')) return; ouvrir(e.target.closest('tr[data-id]')); });
    $('#resultats').addEventListener('keydown', e => { if (e.key === 'Enter') ouvrir(e.target.closest('tr[data-id]')); });
    $('#voile').onclick = fermer;
    document.addEventListener('keydown', e => { if (e.key === 'Escape') fermer(); });
    window.addEventListener('hashchange', () => { const avant = etat.cat; const s = depuisHash(); if (etat.cat !== avant) { etat.cmp.clear(); barreComparaison(); } if (etat.cat === 'feu') { majFacettes(s); ecrireEtat(s); } rendreGroupes(); rendreFiltresCat(); run(); });
    $('#export').onclick = exporterCSV;
    $('#partager').onclick = async () => { try { await navigator.clipboard.writeText(location.href); $('#partager').textContent = 'Lien copié'; setTimeout(() => { $('#partager').textContent = 'Copier le lien'; }, 1500); } catch (_) { prompt('Lien :', location.href); } };
    run();
  } catch (e) {
    $('#statut').textContent = 'Erreur : ' + e.message;
    console.error(e);
  }
}
init();
