#!/usr/bin/env python3
"""Exécute toutes les requêtes de queries/filtres.sql sur la base et affiche un extrait.
Échoue (code 1) si une requête lève une erreur ou si une requête marquée attendue non vide est vide."""
import json, os, re, sqlite3, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(ROOT, 'db', 'forster_pv.sqlite')
SQL = open(os.path.join(ROOT, 'queries', 'filtres.sql'), encoding='utf-8').read()


def parse(text):
    blocks = re.split(r'^-- name: ', text, flags=re.M)[1:]
    for b in blocks:
        name = b.split('\n', 1)[0].strip()
        params = json.loads(re.search(r'^-- params: (.*)$', b, re.M).group(1))
        body = '\n'.join(l for l in b.split('\n')[1:] if not l.startswith('--')).strip().rstrip(';')
        yield name, params, body


def main(verbose='-v' in sys.argv):
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    fail = 0
    out = []
    for name, params, sql in parse(SQL):
        try:
            rows = con.execute(sql, {k.lstrip(':'): v for k, v in params.items()}).fetchall()
        except Exception as e:
            print(f'ECHEC {name}: {e}')
            fail += 1
            continue
        print(f'{name:32s} {len(rows):4d} ligne(s)')
        if len(rows) == 0:
            fail += 1
            print('   -> vide (attendu non vide)')
        out.append({'requete': name, 'parametres': params, 'nb_lignes': len(rows),
                    'extrait': [dict(r) for r in rows[:3]]})
        if verbose:
            for r in rows[:3]:
                print('   ', dict(r))
    with open(os.path.join(ROOT, 'queries', 'resultats_exemple.json'), 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    sys.exit(1 if fail else 0)


if __name__ == '__main__':
    main()
