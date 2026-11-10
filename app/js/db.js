// Chargement de la base SQLite dans le navigateur via sql.js (WebAssembly).
// - fetch du fichier .sqlite versionné dans le dépôt
// - cache navigateur (Cache API) invalidé par la version de données (data/export/manifest.json -> meta.data_sha256)
// - vérification de compatibilité du schéma (meta_schema.schema_version, majeure attendue)
const SQLJS_VERSION = '1.10.3';
const SQLJS_CDN = `https://cdn.jsdelivr.net/npm/sql.js@${SQLJS_VERSION}/dist/`;
export const DB_URL = '../db/forster_pv.sqlite';
const MANIFEST_URL = '../data/export/manifest.json';
export const SCHEMA_MAJOR_ATTENDUE = 1;

function loadScript(src) {
  return new Promise((ok, ko) => {
    const s = document.createElement('script');
    s.src = src; s.onload = ok; s.onerror = () => ko(new Error('Chargement impossible : ' + src));
    document.head.appendChild(s);
  });
}

async function fetchDbBytes(version) {
  const url = `${DB_URL}?v=${encodeURIComponent(version)}`;
  try {
    const cache = await caches.open('forster-pv-db');
    const hit = await cache.match(url);
    if (hit) return new Uint8Array(await hit.arrayBuffer());
    const resp = await fetch(url);
    if (!resp.ok) throw new Error(`HTTP ${resp.status} sur ${DB_URL}`);
    await cache.put(url, resp.clone());
    // purge des anciennes versions
    for (const req of await cache.keys()) if (req.url !== new URL(url, location.href).href) cache.delete(req);
    return new Uint8Array(await resp.arrayBuffer());
  } catch (e) {
    // Cache API indisponible (file://, navigation privée) : fetch direct
    const resp = await fetch(url);
    if (!resp.ok) throw e;
    return new Uint8Array(await resp.arrayBuffer());
  }
}

export async function openDatabase(onStatus = () => {}) {
  onStatus('Chargement du moteur SQLite…');
  if (!window.initSqlJs) await loadScript(SQLJS_CDN + 'sql-wasm.js');
  const SQL = await window.initSqlJs({ locateFile: f => SQLJS_CDN + f });
  let version = 'dev';
  try { version = (await (await fetch(MANIFEST_URL, { cache: 'no-cache' })).json()).meta.data_sha256.slice(0, 12); } catch (_) {}
  onStatus('Téléchargement de la base…');
  const db = new SQL.Database(await fetchDbBytes(version));
  db.exec('PRAGMA foreign_keys = ON');
  const meta = Object.fromEntries(all(db, 'SELECT cle, valeur FROM meta_schema').map(r => [r.cle, r.valeur]));
  const major = parseInt((meta.schema_version || '0').split('.')[0], 10);
  if (major !== SCHEMA_MAJOR_ATTENDUE) throw new Error(`Schéma v${meta.schema_version} incompatible (majeure ${SCHEMA_MAJOR_ATTENDUE} attendue)`);
  return { db, meta };
}

// Exécute une requête paramétrée et renvoie un tableau d'objets
export function all(db, sql, params = {}) {
  const st = db.prepare(sql);
  try {
    st.bind(params);
    const rows = [];
    while (st.step()) rows.push(st.getAsObject());
    return rows;
  } finally { st.free(); }
}
