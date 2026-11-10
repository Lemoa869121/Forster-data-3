#!/usr/bin/env python3
"""Génère docs/04_DICTIONNAIRE_CHAMPS.md et docs/05_REFERENTIELS.md à partir de la base
(types, contraintes, clés, exemple réel par colonne). À relancer après toute évolution du schéma."""
import os, re, sqlite3

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
con = sqlite3.connect(os.path.join(ROOT, 'db', 'forster_pv.sqlite'))
schema_sql = open(os.path.join(ROOT, 'db', 'schema.sql'), encoding='utf-8').read()


def table_ddl(t):
    m = re.search(r'CREATE TABLE ' + t + r'\s*\((.*?)\n\);', schema_sql, re.S)
    if m:
        return m.group(1)
    m = re.search(r'CREATE TABLE ' + t + r'\s*\((.*?)\);', schema_sql, re.S)
    return m.group(1) if m else ''


def col_rule(ddl, col):
    for line in ddl.split('\n'):
        l = line.strip()
        if re.match(r'^' + col + r'\b', l):
            rule = []
            if 'PRIMARY KEY' in l: rule.append('PK')
            if 'NOT NULL' in l: rule.append('NOT NULL')
            if 'UNIQUE' in l: rule.append('UNIQUE')
            m = re.search(r'REFERENCES (\w+)\((\w+)\)', l)
            if m: rule.append(f'FK → {m.group(1)}.{m.group(2)}')
            m = re.search(r'DEFAULT ([^ ,]+)', l)
            if m: rule.append(f'défaut {m.group(1)}')
            m = re.search(r'CHECK \((.*)\)', l)
            if m: rule.append('CHECK ' + m.group(1).replace('|', '\\|')[:90])
            com = l.split('--', 1)[1].strip() if '--' in l else ''
            return '; '.join(rule), com
    return '', ''


tables = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
out = ['# 6. Dictionnaire des champs', '',
       'Généré automatiquement par `scripts/gen_docs.py` depuis `db/schema.sql` et la base. Exemple = première valeur non nulle réelle.', '']
for t in [x for x in tables if not x.startswith('ref_')]:
    n = con.execute(f'SELECT count(*) FROM {t}').fetchone()[0]
    ddl = table_ddl(t)
    out += [f'## `{t}` ({n} lignes)', '', '| Colonne | Type | Règle | Commentaire | Exemple |', '|---|---|---|---|---|']
    for cid, name, typ, notnull, dflt, pk in con.execute(f'PRAGMA table_info({t})'):
        rule, com = col_rule(ddl, name)
        ex = con.execute(f'SELECT {name} FROM {t} WHERE {name} IS NOT NULL LIMIT 1').fetchone()
        ex = '' if ex is None else str(ex[0]).replace('|', '\\|').replace('\n', ' ')[:70]
        out.append(f'| {name} | {typ} | {rule} | {com.replace("|", "/")} | {ex} |')
    out.append('')
open(os.path.join(ROOT, 'docs', '04_DICTIONNAIRE_CHAMPS.md'), 'w', encoding='utf-8').write('\n'.join(out))

out = ['# 7. Référentiels contrôlés', '', 'Tables `ref_*` — valeurs initiales dans `db/referentiels.sql`. Toute colonne `*_code` du schéma pointe vers l\'une d\'elles (clé étrangère).', '']
for t in [x for x in tables if x.startswith('ref_')]:
    cols = [c[1] for c in con.execute(f'PRAGMA table_info({t})')]
    out += [f'## `{t}`', '', '| ' + ' | '.join(cols) + ' |', '|' + '---|' * len(cols)]
    for r in con.execute(f'SELECT * FROM {t}'):
        out.append('| ' + ' | '.join('' if v is None else str(v).replace('|', '/') for v in r) + ' |')
    out.append('')
open(os.path.join(ROOT, 'docs', '05_REFERENTIELS.md'), 'w', encoding='utf-8').write('\n'.join(out))
print('docs générées')

# ---- 09 Requêtes : description, paramètres, tables, extrait de résultat réel ----
import json
res = {r['requete']: r for r in json.load(open(os.path.join(ROOT, 'queries', 'resultats_exemple.json'), encoding='utf-8'))}
sqltxt = open(os.path.join(ROOT, 'queries', 'filtres.sql'), encoding='utf-8').read()
out = ['# 11. Requêtes SQL de filtre (sql.js)', '',
       'Source exécutable : [`queries/filtres.sql`](../queries/filtres.sql). Toutes testées par `scripts/test_queries.py` ; '
       'extraits réels ci-dessous (3 premières lignes). En JS : `db.prepare(sql).bind({":ref": "907724"})`.', '']
for b in re.split(r'^-- name: ', sqltxt, flags=re.M)[1:]:
    name = b.split('\n', 1)[0].strip()
    desc = re.search(r'^-- desc: (.*)$', b, re.M).group(1)
    params = re.search(r'^-- params: (.*)$', b, re.M).group(1)
    body = '\n'.join(l for l in b.split('\n')[1:] if not l.startswith('--')).strip()
    tabs = sorted(set(re.findall(r'(?:FROM|JOIN)\s+(\w+)', body)))
    r = res.get(name, {})
    out += [f'## {name}', '', desc, '', f'- **Paramètres (interface)** : `{params}`', f'- **Tables / vues** : {", ".join("`"+t+"`" for t in tabs)}',
            f'- **Résultat sur le corpus** : {r.get("nb_lignes", "?")} ligne(s)', '', '```sql', body, '```', '']
    if r.get('extrait'):
        out += ['Exemple de résultat :', '', '```json', json.dumps(r['extrait'][:2], ensure_ascii=False, indent=1)[:1800], '```', '']
open(os.path.join(ROOT, 'docs', '09_REQUETES_FILTRES.md'), 'w', encoding='utf-8').write('\n'.join(out))

# ---- 13 annexe : liste des contrôles ouverts ----
rows = con.execute("""SELECT coalesce(d.numero_normalise,'—'), ch.type_code, ch.description, coalesce(sp.page_doc,''), coalesce(sp.section, sp.planche, '')
                      FROM controle_humain ch LEFT JOIN document d ON d.id=ch.document_id LEFT JOIN source_page sp ON sp.id=ch.source_page_id
                      ORDER BY 1, 2""").fetchall()
out = ['# Annexe — points de contrôle humain ouverts (table `controle_humain`)', '', f'{len(rows)} points générés pendant l\'extraction des 6 fichiers.', '',
       '| Document | Type | Description | Page | Section / planche |', '|---|---|---|---|---|']
out += ['| ' + ' | '.join(str(x).replace('|', '/') for x in r) + ' |' for r in rows]
open(os.path.join(ROOT, 'docs', '13b_CONTROLES_OUVERTS.md'), 'w', encoding='utf-8').write('\n'.join(out))
print('docs 09 et 13b générées')

# ---- 13 Exemple d'extraction atomisée : extension 22/2 du PV 11-A-507 (toutes tables) ----
con.row_factory = sqlite3.Row
D = 'DOC-11-A-507-EXT-22-2'
ex = {}
def rows(t, where, p=(D,)):
    r = [dict(x) for x in con.execute(f'SELECT * FROM {t} WHERE {where}', p)]
    if r: ex[t] = r
rows('document', 'id = ?'); rows('source_page', 'document_id = ?'); rows('document_relation', 'document_source_id = ?')
rows('document_organisme', 'document_id = ?'); rows('document_signataire', 'document_id = ?'); rows('document_essai', 'document_id = ?')
rows('essai', 'id IN (SELECT essai_id FROM document_essai WHERE document_id = ?)')
rows('essai_resultat', 'essai_id IN (SELECT essai_id FROM document_essai WHERE document_id = ?)')
rows('configuration', 'document_id = ?'); rows('document_composant', 'document_id = ?')
rows('dc_serrure', 'document_composant_id IN (SELECT id FROM document_composant WHERE document_id = ?)')
rows('caracteristique_document', 'document_composant_id IN (SELECT id FROM document_composant WHERE document_id = ?)')
rows('reference_composant', 'id IN (SELECT reference_id FROM document_composant WHERE document_id = ?)')
rows('restriction', 'document_id = ?')
os.makedirs(os.path.join(ROOT, 'data', 'export', 'exemples'), exist_ok=True)
json.dump(ex, open(os.path.join(ROOT, 'data', 'export', 'exemples', 'extension_22-2_PV_11-A-507.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
pv = {}
for t, w in [('performance', "document_id='DOC-11-A-507'"), ('perf_feu', "performance_id IN (SELECT id FROM performance WHERE document_id='DOC-11-A-507')"),
             ('dimension_format', "document_id='DOC-11-A-507' AND objet_code='passage_libre' AND configuration_id='CFG-11-A-507-BP1'"),
             ('dimension', "format_id IN (SELECT id FROM dimension_format WHERE document_id='DOC-11-A-507' AND objet_code='passage_libre' AND configuration_id='CFG-11-A-507-BP1')"),
             ('document_composant', "document_id='DOC-11-A-507' AND (reference_brute='907724' OR parent_id IN (SELECT id FROM document_composant WHERE document_id='DOC-11-A-507' AND reference_brute='907724' AND configuration_id='CFG-11-A-507-BP1')) AND configuration_id='CFG-11-A-507-BP1'"),
             ('dc_serrure', "document_composant_id IN (SELECT id FROM document_composant WHERE document_id='DOC-11-A-507' AND reference_brute='907724' AND configuration_id='CFG-11-A-507-BP1')"),
             ('controle_humain', "document_id='DOC-11-A-507' AND table_cible='performance'")]:
    pv[t] = [dict(x) for x in con.execute(f'SELECT * FROM {t} WHERE {w}')]
json.dump(pv, open(os.path.join(ROOT, 'data', 'export', 'exemples', 'PV_11-A-507_extrait.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('exemples générés')
