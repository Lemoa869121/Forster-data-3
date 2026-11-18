#!/usr/bin/env python3
"""Régénère db/forster_pv.sqlite à partir de :
   db/schema.sql + db/referentiels.sql + data/sources/catalogue.json + data/sources/documents/*.json

Reproductible : la base est supprimée puis recréée ; l'ordre d'insertion suit les dépendances.
Usage : python3 scripts/build_db.py [--out db/forster_pv.sqlite]
"""
import argparse, glob, json, os, sqlite3, sys, unicodedata, datetime, hashlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHEMA_VERSION = '1.1.0'

# Ordre de chargement (respecte les clés étrangères)
ORDER_CATALOGUE = ['organisme', 'organisme_alias', 'intervenant', 'norme', 'systeme', 'reference_composant']
ORDER_DOCS_1 = ['fichier_source', 'document']
ORDER_DOCS_2 = ['source_page', 'document_relation', 'document_organisme', 'document_signataire', 'document_norme',
                'document_systeme', 'configuration', 'performance', 'perf_feu', 'perf_effraction', 'perf_balistique',
                'perf_aev', 'perf_acoustique', 'document_composant', 'caracteristique_document', 'dc_profile', 'dc_vitrage',
                'dc_serrure', 'dc_articulation', 'dc_ferme_porte', 'dc_joint', 'dc_fixation', 'dimension_format', 'dimension',
                'support_pose', 'restriction', 'controle_humain']
ORDER_AFTER = ['essai', 'essai_resultat', 'document_essai', 'reference_alias', 'enrichissement_externe']


def strip_accents(s):
    return ''.join(c for c in unicodedata.normalize('NFKD', s) if not unicodedata.combining(c)).lower()


def load_catalogues():
    """catalogue.json (manuel) puis catalogue_auto.json : une clé primaire déjà vue est ignorée (le manuel prime)."""
    out = {}
    for name in ['catalogue.json', 'catalogue_auto.json']:
        p = os.path.join(ROOT, 'data', 'sources', name)
        if not os.path.exists(p):
            continue
        for t, rows in json.load(open(p, encoding='utf-8')).items():
            out.setdefault(t, []).extend(rows)
    return out


def merge_documents(docs):
    """Un même document peut être « cité » (present_dans_corpus=0) dans un fichier et fourni dans un autre :
    la version fournie remplace la ligne citée. Deux versions fournies : la première (manuelle) prime."""
    best = {}
    for d in docs:
        for r in d.get('document', []):
            cur = best.get(r['id'])
            if cur is None or (cur['present_dans_corpus'] == 0 and r['present_dans_corpus'] == 1):
                best[r['id']] = r
    for d in docs:
        d['document'] = [r for r in d.get('document', []) if best.get(r['id']) is r]


def dedupe(con, docs):
    """Supprime les doublons de clé primaire entre fichiers (première occurrence conservée)."""
    seen = {}
    n = 0
    for d in docs:
        for t, rows in d.items():
            if t == 'document':
                continue
            pk = [c[1] for c in con.execute(f'PRAGMA table_info({t})') if c[5]]
            if not pk:
                continue
            s = seen.setdefault(t, set())
            keep = []
            for r in rows:
                k = tuple(r.get(c) for c in pk)
                if k in s:
                    n += 1
                    continue
                s.add(k)
                keep.append(r)
            d[t] = keep
    if n:
        print(f'(doublons de clé ignorés : {n})')


def insert_rows(con, table, rows):
    if not rows:
        return 0
    cols = list(rows[0].keys())
    sql = f'INSERT INTO {table} ({",".join(cols)}) VALUES ({",".join("?" * len(cols))})'
    for r in rows:
        if list(r.keys()) != cols:
            raise SystemExit(f'Colonnes hétérogènes dans {table}: {r}')
        for k, v in r.items():
            if v == '':
                raise SystemExit(f'Chaîne vide interdite ({table}.{k}) : utiliser null')
        try:
            con.execute(sql, [r[c] for c in cols])
        except sqlite3.IntegrityError as e:
            raise SystemExit(f'Erreur d\'intégrité dans {table} : {e}\nLigne : {r}')
    return len(rows)


def build_search_index(con):
    con.execute('DELETE FROM recherche_index')
    q = {
        'document': "SELECT id, id, coalesce(numero,'')||' '||numero_normalise||' '||coalesce(objet,'')||' '||type_code FROM document",
        'document_composant': """SELECT dc.id, dc.document_id, coalesce(dc.reference_brute,'')||' '||coalesce(rc.reference_normalisee,'')||' '||
                                 dc.designation_document||' '||dc.categorie_code||' '||coalesce(o.nom,'')||' '||coalesce(dc.condition_texte,'')
                                 FROM document_composant dc LEFT JOIN reference_composant rc ON rc.id=dc.reference_id
                                 LEFT JOIN organisme o ON o.id=rc.fabricant_id""",
        'restriction': "SELECT id, document_id, libelle||' '||coalesce(texte_source,'') FROM restriction",
        'configuration': "SELECT id, document_id, libelle FROM configuration",
    }
    n = 0
    for typ, sql in q.items():
        for oid, did, txt in con.execute(sql).fetchall():
            con.execute('INSERT INTO recherche_index VALUES (?,?,?,?)', (typ, oid, did, strip_accents(txt)))
            n += 1
    return n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=os.path.join(ROOT, 'db', 'forster_pv.sqlite'))
    a = ap.parse_args()
    if os.path.exists(a.out):
        os.remove(a.out)
    con = sqlite3.connect(a.out)
    con.execute('PRAGMA foreign_keys = ON')
    con.executescript(open(os.path.join(ROOT, 'db', 'schema.sql'), encoding='utf-8').read())
    con.executescript(open(os.path.join(ROOT, 'db', 'referentiels.sql'), encoding='utf-8').read())

    cat = load_catalogues()
    # fichiers manuels d'abord (ils priment), puis fichiers AUTO-*
    paths = sorted(glob.glob(os.path.join(ROOT, 'data', 'sources', 'documents', '*.json')), key=lambda p: (os.path.basename(p).startswith('AUTO-'), p))
    docs = [json.load(open(p, encoding='utf-8')) for p in paths]
    merge_documents(docs)
    dedupe(con, docs)
    counts = {}
    con.execute('BEGIN')
    for t in ORDER_CATALOGUE:
        pk = [c[1] for c in con.execute(f'PRAGMA table_info({t})') if c[5]]
        seen_k, uniq = set(), []
        for r in cat.get(t, []):
            k = tuple(r.get(c) for c in pk)
            if k not in seen_k:
                seen_k.add(k); uniq.append(r)
        counts[t] = insert_rows(con, t, uniq)
    for t in ORDER_DOCS_1:
        counts[t] = sum(insert_rows(con, t, d.get(t, [])) for d in docs)
    for t in ORDER_DOCS_2:
        if t in ('document_composant',):
            # parents avant enfants (parent_id)
            rows = [r for d in docs for r in d.get(t, [])]
            rows.sort(key=lambda r: r['parent_id'] is not None)
            counts[t] = insert_rows(con, t, rows)
        else:
            counts[t] = sum(insert_rows(con, t, d.get(t, [])) for d in docs)
    for t in ORDER_AFTER:
        src = cat.get(t, []) + [r for d in docs for r in d.get(t, [])]
        pk = [c[1] for c in con.execute(f'PRAGMA table_info({t})') if c[5]]
        seen_k, uniq = set(), []
        for r in src:
            k = tuple(r.get(c) for c in pk)
            if k not in seen_k:
                seen_k.add(k); uniq.append(r)
        src = uniq
        counts[t] = insert_rows(con, t, src)
    counts['recherche_index'] = build_search_index(con)
    h = hashlib.sha256()
    for p in sorted(glob.glob(os.path.join(ROOT, 'data', 'sources', '*.json'))) + sorted(glob.glob(os.path.join(ROOT, 'data', 'sources', 'documents', '*.json'))):
        h.update(open(p, 'rb').read())
    for k, v in [('schema_version', SCHEMA_VERSION), ('data_sha256', h.hexdigest()),
                 ('genere_le', datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat()),
                 ('nb_fichiers_sources', str(len(docs)))]:
        con.execute('INSERT INTO meta_schema VALUES (?,?)', (k, v))
    con.commit()
    bad = con.execute('PRAGMA foreign_key_check').fetchall()
    if bad:
        raise SystemExit(f'Clés étrangères invalides : {bad[:20]}')
    ok = con.execute('PRAGMA integrity_check').fetchone()[0]
    if ok != 'ok':
        raise SystemExit(f'integrity_check : {ok}')
    con.execute('ANALYZE')
    con.execute('VACUUM')
    con.close()
    for k, v in counts.items():
        print(f'{k:28s} {v:6d}')
    print(f'-> {os.path.relpath(a.out, ROOT)} ({os.path.getsize(a.out) // 1024} Ko)')


if __name__ == '__main__':
    main()
