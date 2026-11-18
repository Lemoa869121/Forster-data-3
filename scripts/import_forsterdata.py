#!/usr/bin/env python3
"""Importe la base ForsterData (export Glide publié : data/sources/forsterdata/data.json) comme couche distincte.

- 1 fiche par ligne (table fiche_forsterdata), rattachée au pseudo-document DOC-FORSTERDATA (type synthese_fabricant).
- Rapprochement de chaque fiche au PV / rapport du corpus par son numéro (exact / partiel / non trouvé).
- Liens de cumul Feu / RC / FB selon la règle ForsterData (même série + même famille d'ouvrage + déclaration
  dans « Cumul de perf », le plus spécifique faisant foi : FB > RC > Feu) -> lien_forsterdata + cumul_performance
  (statut 'declare_fabricant').
- Contrôle croisé : classe de la fiche ≠ classe extraite du document rapproché -> controle_humain 'incoherence'.

Lit la base courante (pour les numéros et classes) : lancer après un premier build, puis rebâtir.
  python3 scripts/build_db.py && python3 scripts/import_forsterdata.py && python3 scripts/build_db.py
"""
import json, os, re, sqlite3, unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'data', 'sources', 'forsterdata', 'data.json')
OUT = os.path.join(ROOT, 'data', 'sources', 'documents', 'FD-forsterdata.json')
DOC = 'DOC-FORSTERDATA'
DOMAINE = {'feu': 'feu', 'rc': 'effraction', 'fb': 'balistique', 'aev': 'aev', 'acoustique': 'acoustique'}
PRIO = {'feu': 0, 'rc': 1, 'fb': 2}


def norm(s):
    return ''.join(c for c in unicodedata.normalize('NFKD', str(s or '')) if not unicodedata.combining(c)).lower().strip()


def alnum(s):
    return re.sub(r'[^A-Z0-9]', '', norm(s).upper())


def systeme(serie):
    s = norm(serie)
    for pat, sid in [(r'unico ?/ ?unico xs', 'SYS-UNICO'), (r'unico ?xs', 'SYS-UNICO-XS'), (r'unico', 'SYS-UNICO'),
                     (r'presto ?xs', 'SYS-PRESTO-XS'), (r'presto ?60', 'SYS-PRESTO-60'), (r'presto ?50', 'SYS-PRESTO-50'),
                     (r'presto', 'SYS-PRESTO'), (r'fuego light ?30', 'SYS-FUEGO-LIGHT-30'), (r'fuego light ?60', 'SYS-FUEGO-LIGHT-60'),
                     (r'fuego light ?90', 'SYS-FUEGO-LIGHT-90'), (r'fuego light ?120', 'SYS-FUEGO-LIGHT-120'), (r'fuego', 'SYS-FUEGO-LIGHT'),
                     (r'thermfix vario', 'SYS-THERMFIX-VARIO'), (r'thermfix light', 'SYS-THERMFIX-LIGHT'), (r'omnia', 'SYS-OMNIA')]:
        if re.search(pat, s):
            return sid
    return None


def famille(type_chassis):  # identique à famille() de ForsterData (index.html)
    t = norm(type_chassis)
    if re.match(r'^porte d\.?a\.?s', t): return 'porte das'
    if re.match(r'^porte va-et-vient', t): return 'porte va-et-vient'
    if re.match(r'^porte', t): return 'porte'
    if re.match(r'^ouvrant', t): return 'ouvrant'
    if 'bords' in t: return 'cloison bords-a-bords'
    if re.match(r'^cloison', t): return 'cloison'
    if re.match(r'^mur', t): return 'mur rideau'
    return t


def typologie(type_chassis):
    t = norm(type_chassis)
    for pat, code in [(r'coulissant', 'porte_coulissante'), (r'^porte|^ouvrant', 'bloc_porte'), (r'bords', 'cloison_vitree_bord_a_bord'),
                      (r'^cloison', 'cloison_vitree'), (r'^mur', 'facade_vitree'), (r'verri', 'verriere'), (r'plancher', 'plancher_vitre'),
                      (r'fen[eê]tre|projection|anglaise|soufflet|^ob|oscillo', 'fenetre'), (r'fixe', 'chassis_fixe')]:
        if re.search(pat, t):
            return code
    return None


def classe_fiche(cat, r):
    if cat == 'feu':
        return re.sub(r'\s+', ' ', str(r.get('Degré feu') or '')).strip().upper() or None
    if cat in ('rc', 'fb'):
        return re.sub(r'\s', '', str(r.get('Classe') or '')).upper().replace('CR', 'RC') or None
    if cat == 'aev':
        a, e, v = (str(r.get(k) or '').strip() for k in ('A', 'E', 'V'))
        vt = str(r.get('V type abc') or '').strip()
        return ' '.join(x for x in (a and f'A*{a[1:]}', e and f'E*{e[1:]}', v and f'V*{vt}{v[1:]}') if x) or None
    if cat == 'acoustique':
        return f"Rw {r['Rw']} dB" if r.get('Rw') not in (None, '') else None


def perf_cle(cat, r):  # performance complète pour les liens (EI30, RC2, FB4-NS)
    if cat == 'feu':
        return re.sub(r'\s', '', str(r.get('Degré feu') or '')).upper()
    c = re.sub(r'\s', '', str(r.get('Classe') or '')).upper().replace('CR', 'RC')
    return re.sub(r'^(FB\d)(N?S)$', r'\1-\2', c)


def declare(txt):
    t = str(txt or '').upper()
    d = {'feu': set(), 'rc': set(), 'fb': set()}
    for m in re.finditer(r'(?<![A-Z0-9])(EI|E)\s?(30|60|90|120)(?!\d)', t): d['feu'].add(m.group(1) + m.group(2))
    for m in re.finditer(r'(?<![A-Z0-9])(?:RC|CR)\s?([1-6])(?!\d)', t): d['rc'].add('RC' + m.group(1))
    for m in re.finditer(r'(?<![A-Z0-9])(?:FB|BR)\s?([4-7])(?:\s*-?\s*(NS|S)(?![A-Z]))?', t):
        d['fb'].add('FB' + m.group(1) + ('-' + m.group(2) if m.group(2) else ''))
    return d


def decl_match(cat, decl, classe):
    if cat != 'fb':
        return classe in decl
    return any(x == classe or ('-' not in x and classe.startswith(x + '-')) for x in decl)


def num(v):
    try:
        return float(v) if v not in (None, '', '-') else None
    except (TypeError, ValueError):
        return None


def main():
    data = json.load(open(SRC, encoding='utf-8'))
    con = sqlite3.connect(os.path.join(ROOT, 'db', 'forster_pv.sqlite'))
    docs = con.execute("SELECT id, numero_normalise, type_code FROM document WHERE present_dans_corpus = 1 AND id <> ?", (DOC,)).fetchall()
    index = [(alnum(re.sub(r'-\d$', '', n)), i, t) for i, n, t in docs if len(alnum(n)) >= 6]
    # classes extraites par document (avec extensions / reconductions pour les PV feu)
    cls_doc = {}
    for did, dom, c in con.execute("""SELECT r.pv_principal_id, p.domaine_code, p.classe_normalisee FROM v_document_rattachement r
                                      JOIN performance p ON p.document_id = r.document_id"""):
        cls_doc.setdefault((did, dom), set()).add(c)
    out = {'document': [{'id': DOC, 'numero': 'ForsterData', 'numero_normalise': 'FORSTERDATA', 'revision': None, 'type_code': 'synthese_fabricant',
                         'domaine_code': 'feu', 'objet': "Base ForsterData (Glide) : fiches Feu, Anti-effraction, Pare-balles, AEV, Acoustique saisies par Forster",
                         'laboratoire_id': None, 'date_emission': data.get('generated'), 'date_validite': None, 'validite_liee_au_pv': 0, 'nb_pages': None,
                         'arrete_reference': None, 'numeros_affaire': None, 'fichier_source_id': None, 'ordre_dans_fichier': None, 'present_dans_corpus': 1,
                         'statut_extraction': 'extrait', 'commentaire': 'Source : https://lemoa869121.github.io/forsterdata/ (data/data.json). Couche Forster distincte des documents de laboratoire.'}],
           'fiche_forsterdata': [], 'lien_forsterdata': [], 'cumul_performance': [], 'controle_humain': []}
    fiches = {}
    stats = {'exact': 0, 'partiel': 0, 'non_trouve': 0, 'incoherences': 0}
    for cat in data['categories']:
        cid = cat['id']
        for i, r in enumerate(cat['rows'], 1):
            fid = f'FD-{cid.upper()}-{i:03d}'
            npv = str(r.get('n° PV') or '').strip()
            key = alnum(npv)
            best, mode, blen = None, 'non_trouve', 0
            for k, did, typ in index:
                if not key:
                    break
                if k == key:
                    best, mode = did, 'exact'; break
                if cid == 'feu' and typ != 'pv_classement':
                    continue
                if k in key and (best is None or len(k) > blen):
                    best, mode, blen = did, 'partiel', len(k)
                elif len(key) >= 7 and key in k and best is None:   # « 16130936/Z1 » ⊂ « 161_30936_Z1f »
                    best, mode, blen = did, 'partiel', 0
            stats[mode] += 1
            classe = classe_fiche(cid, r)
            deg = str(r.get('Degré feu') or '')
            m = re.match(r'\s*(EI|EW|E)\s*[12]?\s*(\d+)', deg.upper())
            row = {'id': fid, 'document_id': DOC, 'categorie': cid, 'domaine_code': DOMAINE[cid], 'type_chassis': r.get('Type de châssis') or '—',
                   'famille_ouvrage': famille(r.get('Type de châssis')), 'typologie_code': typologie(r.get('Type de châssis')), 'serie': r.get('Série'),
                   'systeme_id': systeme(r.get('Série')), 'verrier': r.get('Verrier'), 'numero_pv': npv or None, 'document_pv_id': best,
                   'rapprochement': mode, 'classe': classe, 'critere_feu': m.group(1) if (cid == 'feu' and m) else None,
                   'duree_min': int(m.group(2)) if (cid == 'feu' and m) else None,
                   'classe_air': r.get('A') or None, 'classe_eau': r.get('E') or None, 'classe_vent': ((r.get('V type abc') or '') + (r.get('V') or '')[1:]) or None,
                   'rw_db': num(r.get('Rw')), 'c_db': num(r.get('Rw C')), 'ctr_db': num(r.get('Rw Ctr')),
                   'largeur_verre_mm': num(r.get('Largeur Verre')), 'hauteur_verre_mm': num(r.get('Hauteur Verre')), 'largeur_1v_mm': num(r.get('Largeur 1V')),
                   'largeur_2v_mm': num(r.get('Largeur 2V')), 'hauteur_bp1v_mm': num(r.get('Hauteur BP1V')), 'hauteur_bp2v_mm': num(r.get('Hauteur BP2V')),
                   'hauteur_cloison_mm': num(r.get('Hauteur Cloison')), 'validite': r.get('Validité') or None,
                   'cumul_perf': (str(r.get('Cumul de perf') or '').strip() or None) if str(r.get('Cumul de perf') or '').strip() not in ('-',) else None,
                   'details_json': json.dumps({k: v for k, v in r.items() if not k.startswith('_')}, ensure_ascii=False)}
            out['fiche_forsterdata'].append(row)
            fiches[fid] = (cid, r, row)
            # contrôle croisé de la classe
            if best and classe:
                ext = cls_doc.get((best, DOMAINE[cid]), set())
                if ext:
                    if cid == 'feu':
                        c0 = re.sub(r'[12]', '', alnum(classe)); ok = any(re.sub(r'[12]', '', alnum(x)) == c0 for x in ext)
                    elif cid == 'rc':
                        ok = any(alnum(x)[-1:] == alnum(classe)[-1:] for x in ext)
                    elif cid == 'fb':
                        ok = any(alnum(x)[:3] == alnum(classe)[:3] for x in ext)
                    elif cid == 'acoustique':
                        ok = any(str(int(row['rw_db'])) in x for x in ext) if row['rw_db'] else True
                    else:
                        ok = any(alnum(classe) == alnum(x) for x in ext)
                    if not ok:
                        stats['incoherences'] += 1
                        out['controle_humain'].append({'id': f'CTRL-{fid}-CLS', 'document_id': DOC, 'table_cible': 'fiche_forsterdata', 'ligne_id': fid,
                            'type_code': 'incoherence', 'description': f"ForsterData {fid} ({r.get('Série')} {r.get('Type de châssis')}) : classe « {classe} » ; "
                            f"document {best} : {', '.join(sorted(ext))}.", 'statut': 'ouvert', 'resolution': None, 'source_page_id': None})
    # liens de cumul (règle ForsterData)
    groupes = {}
    for fid, (cid, r, row) in fiches.items():
        if cid in PRIO:
            groupes.setdefault((norm(r.get('Série')), row['famille_ouvrage']), []).append(fid)
    vus = set()
    for g in groupes.values():
        for a in g:
            for b in g:
                ca, ra, _ = fiches[a]; cb, rb, _ = fiches[b]
                if PRIO[ca] >= PRIO[cb]:
                    continue
                da, db = declare(ra.get('Cumul de perf')), declare(rb.get('Cumul de perf'))
                pa, pb = perf_cle(ca, ra), perf_cle(cb, rb)
                if db[ca]:
                    ok, motif = decl_match(ca, db[ca], pa), f"{b} déclare {', '.join(sorted(db[ca]))}"
                else:
                    ok, motif = decl_match(cb, da[cb], pb), f"{a} déclare {', '.join(sorted(da[cb]))}"
                if not ok:
                    continue
                x, y = sorted((a, b))
                out['lien_forsterdata'].append({'fiche_a': x, 'fiche_b': y, 'motif': motif})
                k = (fiches[a][2]['systeme_id'], fiches[a][2]['typologie_code'], ca, pa, cb, pb)
                if k in vus:
                    continue
                vus.add(k)
                out['cumul_performance'].append({'id': f'CUM-FD-{len(vus):04d}', 'document_id': DOC, 'systeme_id': fiches[a][2]['systeme_id'],
                    'typologie_code': fiches[a][2]['typologie_code'], 'domaine_a': DOMAINE[ca], 'classe_a': pa, 'domaine_b': DOMAINE[cb], 'classe_b': pb,
                    'statut_cumul': 'declare_fabricant', 'condition_texte': f"ForsterData — {ra.get('Série')} / {fiches[a][2]['famille_ouvrage']} ; {motif}",
                    'justificatifs': f"{ra.get('n° PV') or '?'} ; {rb.get('n° PV') or '?'}".replace('\n', ' ')[:300], 'source_page_id': None, 'statut_extraction': 'extrait'})
    json.dump(out, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print({**stats, 'fiches': len(out['fiche_forsterdata']), 'liens': len(out['lien_forsterdata']), 'cumuls': len(out['cumul_performance'])})


if __name__ == '__main__':
    main()
