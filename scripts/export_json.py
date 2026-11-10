#!/usr/bin/env python3
"""Exporte la base SQLite en JSON : un fichier par table (data/export/tables/<table>.json)
et un fichier global (data/export/forster_pv.json) = {meta, tables: {table: [lignes]}}.
Le format par table est EXACTEMENT celui des colonnes du schéma : réimportable tel quel."""
import json, os, sqlite3

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(ROOT, 'db', 'forster_pv.sqlite')
OUT = os.path.join(ROOT, 'data', 'export')


def main():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    tables = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
    os.makedirs(os.path.join(OUT, 'tables'), exist_ok=True)
    meta = {r['cle']: r['valeur'] for r in con.execute('SELECT * FROM meta_schema')}
    glob_ = {'meta': meta, 'tables': {}}
    manifest = []
    for t in tables:
        rows = [dict(r) for r in con.execute(f'SELECT * FROM {t} ORDER BY rowid')]
        cols = [c[1] for c in con.execute(f'PRAGMA table_info({t})')]
        glob_['tables'][t] = rows
        with open(os.path.join(OUT, 'tables', f'{t}.json'), 'w', encoding='utf-8') as f:
            json.dump({'table': t, 'colonnes': cols, 'lignes': rows}, f, ensure_ascii=False, indent=1)
        manifest.append({'table': t, 'nb_lignes': len(rows), 'fichier': f'tables/{t}.json'})
    with open(os.path.join(OUT, 'forster_pv.json'), 'w', encoding='utf-8') as f:
        json.dump(glob_, f, ensure_ascii=False, separators=(',', ':'))
    with open(os.path.join(OUT, 'manifest.json'), 'w', encoding='utf-8') as f:
        json.dump({'meta': meta, 'tables': manifest}, f, ensure_ascii=False, indent=1)
    print(f'{len(tables)} tables exportées -> {os.path.relpath(OUT, ROOT)}')


if __name__ == '__main__':
    main()
