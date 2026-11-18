#!/usr/bin/env python3
"""Extraction automatique des rapports d'essais multi-domaines (dossier « Rapports d'essais »).

Entrée : textes par page (séparateur \\f) produits par scripts/ocr_rapport.sh dans un dossier
         dont le nom de fichier encode le chemin d'origine (« / » remplacé par « __ »).
Sortie : data/sources/documents/RAP-*.json + data/sources/catalogue_rapports.json

Principes (identiques au corpus feu) :
  - une classe n'est enregistrée que si elle figure dans le nom de fichier OU dans le texte ;
    la page où elle est lue est conservée (source_page) ; sinon statut 'non_trouve' / 'a_verifier' ;
  - tout ce qui est produit ici porte un contrôle humain 'extraction_auto' ;
  - un cumul n'est créé que s'il est ÉNONCÉ (même rapport, éprouvette décrite comme coupe-feu,
    ou synthèse Forster) — jamais déduit d'un rapprochement système/typologie.
Usage : python3 scripts/extract_rapports.py <dossier_txt> [--racine "Z:\\...\\Rapports d'essais"]
"""
import argparse, json, os, re, sys, unicodedata, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, 'data', 'sources', 'documents')

DOMAINE_DOSSIER = {
    "Résistance à l'effraction (RC)": 'effraction', "Résistance aux balles (FB)": 'balistique',
    "Resistance à l'explosion (EPR)": 'explosion', 'A.E.V': 'aev', 'Acoustique': 'acoustique',
    'Résistance aux chocs': 'choc', 'Thermique': 'thermique', 'Portes issues de secours': 'issue_secours',
    'Portes grand traffic - Test 1 Mo cycles': 'endurance', "Nuance d'acier gammes Forster": 'endurance',
    'Rapports de classement feu (EN 13501-2)': 'feu', 'Sismique': 'aev', 'Passeports CE': None, 'DTA': None,
}
DTA_SOUS = {'1 Mo Cycles': 'endurance', 'Brouillard salin': 'durabilite', 'Ensoleillement': 'durabilite',
            'Essais mécaniques': 'endurance', 'Etude Thermique': 'thermique', 'Examen metallographique': 'durabilite',
            'Gradient thermique': 'aev', 'QB49': 'durabilite', 'Choc de sécurité': 'choc'}

SYSTEMES = [  # (motif, id) — ordre : le plus spécifique d'abord
    (r'unico[ _-]?xs', 'SYS-UNICO-XS'), (r'unico', 'SYS-UNICO'), (r'presto[ _-]?xs', 'SYS-PRESTO-XS'),
    (r'presto[ _-]?60', 'SYS-PRESTO-60'), (r'presto[ _-]?50|norm ?50', 'SYS-PRESTO-50'), (r'presto[ _]norm|\bnorm\b', 'SYS-NORM'),
    (r'presto', 'SYS-PRESTO'), (r'fuego[ _-]?light|fuegolight', 'SYS-FUEGO-LIGHT'),
    (r'thermfix[ _-]?vario|\btfv\b|thermifix vario', 'SYS-THERMFIX-VARIO'), (r'thermfix[ _-]?light', 'SYS-THERMFIX-LIGHT'),
    (r'omnia', 'SYS-OMNIA'),
]
NOUVEAUX_SYSTEMES = [
    {'id': 'SYS-OMNIA', 'nom': 'Omnia', 'nom_normalise': 'OMNIA', 'fabricant_id': 'ORG-FORSTER', 'isolation_thermique': None,
     'profondeur_mm': None, 'commentaire': 'Système cité uniquement dans les rapports d\'essais (effraction, balistique)'},
    {'id': 'SYS-NORM', 'nom': 'Presto Norm', 'nom_normalise': 'PRESTO NORM', 'fabricant_id': 'ORG-FORSTER', 'isolation_thermique': 0,
     'profondeur_mm': None, 'commentaire': 'Fenêtres Presto « Norm » (AEV, thermique)'},
    {'id': 'SYS-PRESTO', 'nom': 'Presto (série non précisée)', 'nom_normalise': 'PRESTO (SERIE NON PRECISEE)', 'fabricant_id': 'ORG-FORSTER',
     'isolation_thermique': 0, 'profondeur_mm': None, 'commentaire': None},
]
LABOS = [  # (motif texte/nom, id, nom, pays)
    (r'beschussamt|beshcussamt', 'ORG-BESCHUSSAMT-ULM', 'Beschussamt Ulm', 'DE'),
    (r'fraunhofer|ernst-mach', 'ORG-FRAUNHOFER-EMI', 'Fraunhofer EMI', 'DE'),
    (r'\bKADDB\b', 'ORG-KADDB', 'KADDB', 'JO'),
    (r'\bCNPP\b', 'ORG-CNPP', 'CNPP', 'FR'),
    (r'buildwise', 'ORG-BUILDWISE', 'Buildwise (ex-CSTC)', 'BE'),
    (r'\bCSTC\b|GSFM', 'ORG-BUILDWISE', 'Buildwise (ex-CSTC)', 'BE'),
    (r'\bCEBTP\b|BEB1\.', 'ORG-CEBTP', 'CEBTP (Ginger)', 'FR'),
    (r'\bCSTB\b|DBV-|CLC ?10', 'ORG-CSTB', 'CSTB', 'FR'),
    (r'GBD[ _]?LAB|\bGBD\b|^L2[2-5]_|__L2[2-5]_', 'ORG-GBD-LAB', 'GBD Lab', 'AT'),
    (r'\bPfB\b|PFB -|Prüfinstitut für|Prüfstelle für Fenster', 'ORG-PFB', 'PfB Rosenheim', 'DE'),
    (r'\bPIV\b|Velbert', 'ORG-PIV', 'PIV Velbert', 'DE'),
    (r'\bSGS\b', 'ORG-SGS', 'SGS France', 'FR'),
    (r'\bDMT\b', 'ORG-DMT', 'Laboratoire DMT', None),
    (r'Efectis', 'ORG-EFECTIS-FRANCE', 'Efectis France', 'FR'),
    (r'\bLaSM\b', 'ORG-LASM', 'LaSM', None),
    (r'IS GROUP|Institut de Soudure|P6ETGCP', 'ORG-INSTITUT-SOUDURE', 'Institut de Soudure', 'FR'),
    (r'\bift\b|ift Rosenheim|Institut für Fenstertechnik|-PR0\d|PB-C01|Klasse_', 'ORG-IFT', 'ift Rosenheim', 'DE'),
    (r'Minergie', 'ORG-MINERGIE', 'Minergie', 'CH'),
]
NORMES = {
    'effraction': ('NRM-EN-1627', 'EN 1627'), 'balistique': ('NRM-EN-1522', 'EN 1522'), 'explosion': ('NRM-EN-13123-1', 'EN 13123-1'),
    'aev': ('NRM-EN-14351-1', 'EN 14351-1'), 'acoustique': ('NRM-EN-ISO-717-1', 'EN ISO 717-1'),
    'endurance': ('NRM-EN-1191', 'EN 1191'), 'issue_secours': ('NRM-EN-1125', 'EN 1125'), 'thermique': ('NRM-EN-ISO-10077-2', 'EN ISO 10077-2'),
}
EXCLURE = [r'Plan-3\d\d', r'Datasheet']
# Corrections manuelles connues (copie du même rapport ailleurs dans le dossier, avec un nom plus explicite)
OVERRIDES = {
    '15-0152-01': {'labo': 'ORG-GBD-LAB', 'typo': 'bloc_porte', 'feu': 'EI60',
                   'note': "Même rapport que « GBD LAB_RC4_PORTE TOLEE EI60_15-0152-01_2015.pdf » (dossier Fuego Light/RC4)"},
}

TYPO = [  # sur le chemin + nom de fichier (ordre : le plus discriminant d'abord)
    (r'UP 862|polygard pro|vetroflam|contraflam|seuil de porte|paumelle|Uf_\d|profilé d.appui|valeurs_vitrages|pyrostop rw', 'composant'),
    (r'coulissant|schiebe|hebe', 'porte_coulissante'),
    (r'fen[eê]tre|fenster|window|(?<![a-z])O[BF](?![a-z])|anglaise|projection|soufflet', 'fenetre'),
    (r'porte|t[üu]r(?![a-z])|tuer|door|(?<![a-z])vtl|vantaux|vantail|(?<![a-z0-9])[12] ?v(?![a-z])|flg', 'bloc_porte'),
    (r'verri[eè]re', 'verriere'),
    (r'mur rideau|fa[cç]ade|curtain|thermfix vario|thermifix|(?<![a-z])tfv(?![a-z])', 'facade_vitree'),
    (r'cloison', 'cloison_vitree'),
    (r'ch[aâ]ssis|(?<![a-z])fixes?(?![a-z])|festverglas', 'chassis_fixe'),
]

RE_DATE_NUM = re.compile(r'\b([0-3]?\d)[./]([01]?\d)[./]((?:19|20)\d\d)\b')
MOIS = {'januar': 1, 'janvier': 1, 'january': 1, 'februar': 2, 'février': 2, 'fevrier': 2, 'february': 2, 'märz': 3, 'mars': 3, 'march': 3,
        'april': 4, 'avril': 4, 'mai': 5, 'may': 5, 'juni': 6, 'juin': 6, 'june': 6, 'juli': 7, 'juillet': 7, 'july': 7,
        'august': 8, 'août': 8, 'aout': 8, 'september': 9, 'septembre': 9, 'oktober': 10, 'octobre': 10, 'october': 10,
        'november': 11, 'novembre': 11, 'dezember': 12, 'décembre': 12, 'decembre': 12, 'december': 12}
RE_DATE_TXT = re.compile(r'\b([0-3]?\d)\.?\s+(' + '|'.join(MOIS) + r')\s+((?:19|20)\d\d)\b', re.I)

RE_FEU = re.compile(r'(?<![A-Za-z0-9])(E\s?I\s?[12]?|EW|E)\s?-?\s?(30|60|90|120)(?![0-9])', re.I)


def slug(s):
    s = ''.join(c for c in unicodedata.normalize('NFKD', s) if not unicodedata.combining(c))
    return re.sub(r'[^A-Za-z0-9]+', '-', s).strip('-').upper()


def numero_rapport(nom):
    pats = [r'\d{2}-\d{6}-PR\d{2}(?:_\d)?', r'\d{2}[ -]\d{6}[ -]PR\d{2}', r'\d{2} \d{5,6} PR\d{2}', r'EFR-\d{2}-\d{6}', r'\d{2}[-/]\d{2}-A\d{3}-[BKG]\d',
            r'20\d\d-04-\d{4}[-_][BKG]\d', r'S ?\d{2} ?\d{4} ?\d{2}[-_ ]?[BZ](?![a-z])', r'S\d{8}', r'MD\d{6}[AB]?', r'GSFM[ -]\d{2}-\d{3}-\d{2}',
            r'EF-\d{2}-\d{3}-\d{2}', r'DBV-M?-?\d{2}-\d{4,8}(?:-[A-D])?', r'CLC ?10-\d+', r'BEB1\.[LM]\.\d{4}(?:-\d)?', r'L\d{2}_\d{4}_\d{2}',
            r'\d{2}-\d{4}-FE-\d{3}(?:-\d{3})?', r'I-4\d_17', r'K-\d{4}', r'\d{2}-\d{6}-PB\d{2}', r'1\d\d[ _]\d{5}(?:[_ -]\d)?(?:[ _-]?[RZ]\d{1,2})?f?',
            r'2\d\d \d{5}f?', r'\d{2}-\d{2}-\d{4}', r'\d{2}-\d{4}-\d{2}', r'45-28-21', r'CXL\d{3}-\d{2}', r'a046-k1', r'E03-016',
            r'\d{8}-(?:Z)?\d{1,2}', r'\d{4}-\d{4}', r'\d{8,9}-\d{1,2}', r'\d{8}', r'4518-P6ETGCP-V1', r'25\.005-REY', r'\d{3} \d{5}-\d[a-z]?']
    for p in pats:
        m = re.search(p, nom, re.I)
        if m:
            return m.group(0).strip(' _-')
    return None


def detect_systemes(txt):
    found = []
    low = txt.lower()
    for pat, sid in SYSTEMES:
        if re.search(pat, low) and sid not in found:
            if sid == 'SYS-UNICO' and 'SYS-UNICO-XS' in found and not re.search(r'unico(?![ _-]?xs)', low):
                continue
            if sid == 'SYS-PRESTO' and any(s.startswith('SYS-PRESTO-') or s == 'SYS-NORM' for s in found):
                continue
            found.append(sid)
    return found


def detect_typo(chemin):
    for pat, code in TYPO:
        if re.search(pat, chemin, re.I):
            return code
    return None


def find_page(pages, rx):
    r = re.compile(rx, re.I)
    for i, p in enumerate(pages, 1):
        if r.search(p):
            return i
    return None


def date_doc(pages, annee_nom):
    for p in pages[:3]:
        cands = []
        for m in RE_DATE_NUM.finditer(p):
            d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
            if 1 <= d <= 31 and 1 <= mo <= 12:
                cands.append((y, mo, d))
        for m in RE_DATE_TXT.finditer(p):
            cands.append((int(m.group(3)), MOIS[m.group(2).lower()], int(m.group(1))))
        cands = [c for c in cands if 1995 <= c[0] <= 2026]
        if annee_nom:
            cands = [c for c in cands if c[0] == annee_nom] or []
        if cands:
            y, mo, d = max(cands)
            try:
                return datetime.date(y, mo, d).isoformat()
            except ValueError:
                pass
    return None


chemin_courant = ''


def classes_domaine(dom, nom, pages):
    """Retourne une liste de dict {classe, libelle, page, statut, detail} pour un domaine."""
    txt = '\n'.join(pages)
    out = []

    def add(classe, libelle, rx_txt, detail):
        if any(o['classe'] == classe for o in out):
            return
        page = find_page(pages, rx_txt)
        out.append({'classe': classe, 'libelle': libelle, 'page': page,
                    'statut': 'extrait' if page else 'a_verifier', 'detail': detail})

    if dom == 'effraction':
        src = nom + ' '
        if not re.search(r'(?<![A-Za-z])(RC|CR|WK)\s?[1-6]', src, re.I):
            dossier = [seg for seg in chemin_courant.split('/')[:-1] if re.fullmatch(r'(RC|CR)\s?[1-6]', seg.strip(), re.I)]
            if dossier:
                src = dossier[-1] + ' '
        for m in re.finditer(r'(?<![A-Za-z])(RC|CR|WK)\s?([1-6])(N)?\b', src, re.I):
            k = m.group(1).upper(); n = m.group(2)
            c = ('WK' if k == 'WK' else 'RC') + n + (m.group(3) or '').upper()
            add(c, m.group(0), r'\b(RC|CR|WK)\s?' + n + r'\b|Widerstandsklasse\s?' + n, {'classe_rc': c})
        if not out:
            cs = {}
            for m in re.finditer(r'\b(RC|WK)\s?([1-6])\b', txt):
                c = m.group(1) + m.group(2); cs[c] = cs.get(c, 0) + 1
            for c, n in sorted(cs.items(), key=lambda x: -x[1])[:3]:
                if n >= 2:
                    add(c, c, r'\b' + c[:2] + r'\s?' + c[2:] + r'\b', {'classe_rc': c})
    elif dom == 'balistique':
        for m in re.finditer(r'\b(FB|BR)\s?([1-7])\s?-?\s?(N?S)?(?![A-Za-z0-9])', nom + ' ' + txt[:4000], re.I):
            sfx = (m.group(3) or '').upper()
            c = f'{m.group(1).upper()}{m.group(2)}{sfx}'
            if not sfx and any(o['classe'].startswith(c) for o in out):
                continue
            add(c, m.group(0), m.group(1) + r'\s?' + m.group(2), {'classe': c[:3], 'avec_eclats': sfx or None})
    elif dom == 'explosion':
        for m in re.finditer(r'\bEPR\s?([1-4])\s?-?\s?(N?S)?\b', nom, re.I):
            c = f'EPR{m.group(1)}' + (m.group(2) or '').upper()
            add(c, m.group(0), r'EPR\s?' + m.group(1), {'classe': f'EPR{m.group(1)}', 'avec_eclats': (m.group(2) or '').upper() or None})
        if not out:
            m = re.search(r'\bEPR\s?([1-4])\s?\(?(N?S)?\)?', txt)
            if m:
                add(f'EPR{m.group(1)}' + (m.group(2) or '').upper(), m.group(0), re.escape(m.group(0)),
                    {'classe': f'EPR{m.group(1)}', 'avec_eclats': (m.group(2) or '').upper() or None})
    elif dom == 'aev':
        m = re.search(r'A\*?(\d)[-_ ]E\*?(\d{1,4}A?)[-_ ]?V\*?([ABC])(\d)', nom)
        if m:
            c = f'A*{m.group(1)} E*{m.group(2)} V*{m.group(3)}{m.group(4)}'
            add(c, m.group(0), r'\b' + m.group(2) + r'\b', {'classe_air': m.group(1), 'classe_eau': m.group(2), 'classe_vent': m.group(3) + m.group(4)})
        else:
            for i, p in enumerate(pages[:6]):
                toks = re.findall(r'(?:Klasse|classe|Class)\s*:?\s*([A-Z]?\s?\d{1,4}\s?[AB]?)\b', p)
                if len(toks) < 2:
                    continue
                ca = ce = cv = None
                for t in toks:
                    t = t.replace(' ', '')
                    if ca is None and re.fullmatch(r'[1-4]', t): ca = t
                    elif ce is None and re.fullmatch(r'\d{1,2}[AB]|E\d{3,4}', t): ce = t
                    elif cv is None and re.fullmatch(r'[ABC][1-5]', t): cv = t
                if ca or ce or cv:
                    c = ' '.join(x for x in (ca and f'A*{ca}', ce and f'E*{ce}', cv and f'V*{cv}') if x)
                    out.append({'classe': c, 'libelle': 'tableau de synthèse : ' + c, 'page': i + 1, 'statut': 'a_verifier',
                                'detail': {'classe_air': ca, 'classe_eau': ce, 'classe_vent': cv}})
                    break
    elif dom == 'acoustique':
        vals = []
        for m in re.finditer(r'Rw\s?(?:\(C\s?;\s?C\s?tr\))?\s?=\s?(\d{2})\s?(?:\(\s?(-?\d{1,2})\s?;\s?(-?\d{1,2})\s?\))?\s?dB', txt, re.I):
            vals.append((int(m.group(1)), m.group(2), m.group(3)))
        m = re.search(r'Rw[ _]?(\d{2})\s?(?:_?\((-?\d+);(-?\d+)\))?\s?db', nom, re.I)
        if m:  # valeur annoncée dans le nom : on ne garde qu'elle (les autres Rw du texte = vitrages seuls, variantes…)
            v0 = int(m.group(1))
            same = [v for v in vals if v[0] == v0]
            vals = [same[0] if same else (v0, m.group(2), m.group(3))]
        seen = set()
        for rw, c, ctr in vals:
            if rw in seen or not (25 <= rw <= 60):
                continue
            seen.add(rw)
            lib = f'Rw = {rw} dB' + (f' ({c};{ctr})' if c else '')
            add(f'Rw {rw} dB', lib, r'R\s?w[^\n]{0,30}' + str(rw), {'rw_db': rw, 'c_db': int(c) if c else None, 'ctr_db': int(ctr) if ctr else None})
            if len(seen) >= 6:
                break
    elif dom == 'thermique':
        m = re.search(r'U\s?f\s?=\s?(\d+[.,]\d+)\s?(?:bis|à|-|to)\s?(\d+[.,]\d+)', txt)
        m2 = re.search(r'Uf_\d+ = (\d+[.,]\d+)', nom)
        if m2:
            v = float(m2.group(1).replace(',', '.'))
            add(f'Uf {v} W/(m2.K)', m2.group(0), r'U\s?f', {'grandeur': 'Uf', 'valeur_min': v, 'valeur_max': v, 'unite': 'W/(m2.K)'})
        elif m:
            a, b = float(m.group(1).replace(',', '.')), float(m.group(2).replace(',', '.'))
            add(f'Uf {a}-{b} W/(m2.K)', m.group(0), re.escape(m.group(0)[:6]), {'grandeur': 'Uf', 'valeur_min': a, 'valeur_max': b, 'unite': 'W/(m2.K)'})
    elif dom == 'choc':
        m = re.search(r'(\d{3,4}) ?J\b', nom)
        if m:
            add(f'Choc {m.group(1)} J', m.group(0), m.group(1) + r' ?J', {'grandeur': 'energie_choc', 'valeur_min': float(m.group(1)), 'valeur_max': float(m.group(1)), 'unite': 'J'})
        elif re.search(r'M50|choc de s[ée]curit', nom + txt[:3000], re.I):
            add('Choc de sécurité M50', 'chocs de sécurité (corps mou M50)', r'M50|choc', {'grandeur': 'conformite', 'valeur_min': None, 'valeur_max': None, 'unite': None})
        elif re.search(r'pince', nom, re.I):
            add('Anti-pince-doigts', 'porte anti-pince-doigts', r'pince|Finger|klemm', {'grandeur': 'conformite', 'valeur_min': None, 'valeur_max': None, 'unite': None})
    elif dom == 'endurance':
        m = re.search(r'(?:EN ?12400[^\n]{0,40}?)?Klasse\s?([1-8])\b|classe\s?([1-8])\b', txt)
        k = m and (m.group(1) or m.group(2))
        cyc = re.search(r'(1[ .]?000[ .]?000|500[ .]?000|200[ .]?000|100[ .]?000)\s*(?:Zyklen|cycles|Lastwechsel|Betätigungen)', txt, re.I)
        if k:
            add(f'EN 12400 classe {k}', m.group(0), r'Klasse\s?' + k + r'|classe\s?' + k, {'grandeur': 'classe_endurance', 'valeur_min': float(k), 'valeur_max': float(k), 'unite': None})
        if cyc:
            n = int(re.sub(r'\D', '', cyc.group(1)))
            add(f'{n:,} cycles'.replace(',', ' '), cyc.group(0), re.escape(cyc.group(1)), {'grandeur': 'nb_cycles', 'valeur_min': float(n), 'valeur_max': float(n), 'unite': 'cycles'})
        if not out and re.search(r'1 ?Mo', nom):
            add('1 000 000 cycles', '1 Mo cycles (nom de fichier)', r'1\.?000\.?000|1 000 000', {'grandeur': 'nb_cycles', 'valeur_min': 1e6, 'valeur_max': 1e6, 'unite': 'cycles'})
    elif dom == 'issue_secours':
        for n, lib in (('1125', 'EN 1125 (barre anti-panique)'), ('179', 'EN 179 (poignée / plaque de poussée)')):
            if re.search(r'EN ?' + n + r'\b', nom + txt[:6000]):
                add(f'EN {n}', lib, r'EN ?' + n + r'\b', {'grandeur': 'conformite', 'valeur_min': None, 'valeur_max': None, 'unite': None})
    elif dom == 'feu':
        rxf = re.compile(r'\b(E\s?I\s?([12])?|EW|E)\s?(15|20|30|45|60|90|120)\b')
        p1 = next((i for i, p in enumerate(pages) if rxf.search(p)), None)
        if p1 is not None:
            for m in rxf.finditer(pages[p1]):
                k = re.sub(r'\s', '', m.group(1)).upper()
                c = f'{k} {m.group(3)}'
                if not any(o['classe'] == c for o in out):
                    out.append({'classe': c, 'libelle': m.group(0), 'page': p1 + 1, 'statut': 'extrait', 'detail': {'k': k, 'duree': int(m.group(3))}})
    return out


def perf_detail(dom, pid, d, norme_id):
    if dom == 'effraction':
        return 'perf_effraction', {'performance_id': pid, 'classe_rc': d['classe_rc'], 'norme_id': norme_id, 'duree_resistance_min': None}
    if dom == 'balistique':
        return 'perf_balistique', {'performance_id': pid, 'classe': d['classe'], 'avec_eclats': d['avec_eclats'], 'arme_munition': None, 'norme_id': norme_id}
    if dom == 'explosion':
        return 'perf_explosion', {'performance_id': pid, 'classe': d['classe'], 'avec_eclats': d['avec_eclats'], 'norme_id': norme_id}
    if dom == 'aev':
        return 'perf_aev', {'performance_id': pid, 'classe_air': d['classe_air'], 'classe_eau': d['classe_eau'], 'classe_vent': d['classe_vent'],
                            'pression_air_pa': None, 'pression_eau_pa': None, 'pression_vent_pa': None, 'norme_id': norme_id}
    if dom == 'acoustique':
        return 'perf_acoustique', {'performance_id': pid, 'rw_db': d['rw_db'], 'c_db': d['c_db'], 'ctr_db': d['ctr_db'], 'norme_id': norme_id}
    if dom == 'feu':
        k = d['k']
        return 'perf_feu', {'performance_id': pid, 'critere_r': 0, 'critere_e': 1, 'critere_i': int('I' in k),
                            'variante_i': ('I' + k[-1]) if k[-1] in '12' else ('I' if 'I' in k else None), 'critere_w': int('W' in k),
                            'critere_m': 0, 'critere_c': 0, 'classe_c': None, 'critere_s': 0, 'duree_min': d['duree'], 'sens_feu': None}
    return 'perf_mesure', {'performance_id': pid, 'grandeur': d['grandeur'], 'valeur_min': d['valeur_min'], 'valeur_max': d['valeur_max'],
                           'unite': d['unite'], 'norme_id': norme_id}


def type_doc(nom):
    n = nom.lower()
    if re.search(r'tableau r[ée]cap|r[ée]sum[ée]|r[ée]capitulatif|tab affbl|synth[eè]se aev|synth[eè]se_accessoires|verarbeitungsunterlage|correspondance', n):
        return 'synthese_fabricant'
    if re.search(r'passeport|produktpass|systempass|application_conforme', n):
        return 'passeport_ce'
    if re.search(r'klasse_|^k-\d', n):
        return 'rapport_classement'
    if re.search(r'gutachten|avis|synth[eè]se|correspondance|conformit|verarbeitungsunterlage', n):
        return 'avis_expertise'
    if re.search(r'certifi|zertifi|minergie', n):
        return 'certificat'
    if re.search(r'polygard pro|silencio', n):
        return 'fiche_technique'
    return 'rapport_essai'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('txt_dir')
    ap.add_argument('--racine', default="Z:\\FR-LIE\\Forster-Technique\\Rapports d'essais")
    a = ap.parse_args()
    for f in os.listdir(OUT_DIR):
        if f.startswith('RAP-'):
            os.remove(os.path.join(OUT_DIR, f))
    labos_vus, normes_vues, ids_vus = {}, {}, set()
    stats = {'docs': 0, 'perf': 0, 'cumul': 0, 'ignores': 0}
    for fn in sorted(os.listdir(a.txt_dir)):
        if not fn.endswith('.txt'):
            continue
        chemin = fn[:-4].replace('__', '/')
        nom = chemin.split('/')[-1]
        if any(re.search(p, nom) for p in EXCLURE):
            stats['ignores'] += 1
            continue
        pages = open(os.path.join(a.txt_dir, fn), encoding='utf-8', errors='replace').read().split('\f')
        if pages and not pages[-1].strip():
            pages = pages[:-1]
        top = chemin.split('/')[0]
        dom = DOMAINE_DOSSIER.get(top)
        if top == 'DTA':
            dom = next((v for k, v in DTA_SOUS.items() if k in chemin), None)
        tdoc = type_doc(nom)
        tete = '\n'.join(pages[:3])
        if dom is None and tdoc == 'passeport_ce':
            dom = 'aev'
        if top == 'Sismique':
            dom = 'aev'
        num_auto = numero_rapport(nom)
        num = num_auto or re.sub(r'\s+', ' ', nom.replace('_', ' ')).strip()[:70]
        base = 'DOC-RAP-' + slug(num_auto or nom)[:40].strip('-')
        did = base; i = 2
        while did in ids_vus:
            did = f'{base}-{i}'; i += 1
        ids_vus.add(did)
        my = re.findall(r'(?<!\d)(19[89]\d|20[0-2]\d)(?!\d)', nom)
        annee_nom = int(my[-1]) if my else None
        date = date_doc(pages, annee_nom)
        # laboratoire
        labo = None
        for pat, oid, onom, pays in LABOS:
            if re.search(pat, nom) or re.search(pat, tete[:6000]):
                labo = oid; labos_vus[oid] = (onom, pays); break
        if labo == 'ORG-MINERGIE' or tdoc in ('synthese_fabricant', 'passeport_ce'):
            labo = None if tdoc in ('synthese_fabricant', 'passeport_ce') else labo
        sys_ids = detect_systemes(chemin) or detect_systemes(tete[:5000])
        typo = detect_typo(nom) or detect_typo(chemin)
        ov = OVERRIDES.get(num, {})
        if ov.get('labo'):
            labo = ov['labo']; labos_vus.setdefault(labo, ('GBD Lab', 'AT'))
        typo = ov.get('typo', typo)
        rel = chemin.replace('/', '\\')
        doc = {
            'fichier_source': [{'id': 'FIC-' + did[4:], 'nom_fichier': rel, 'drive_file_id': None, 'url': None,
                                'taille_octets': None, 'date_modification': None, 'code_fournisseur_vitrage': None, 'code_marche': None,
                                'commentaire': f"Rapports d'essais : {a.racine}\\{rel}.pdf"}],
            'document': [{'id': did, 'numero': num, 'numero_normalise': num + ('' if did == base else did[len(base):]), 'revision': None,
                          'type_code': tdoc, 'domaine_code': dom or 'feu', 'objet': nom[:200], 'laboratoire_id': labo,
                          'date_emission': date, 'date_validite': None, 'validite_liee_au_pv': 0, 'nb_pages': len(pages) or None,
                          'arrete_reference': None, 'numeros_affaire': None, 'fichier_source_id': 'FIC-' + did[4:], 'ordre_dans_fichier': 1,
                          'present_dans_corpus': 1, 'statut_extraction': 'a_verifier',
                          'commentaire': f"Extraction automatique (rapports d'essais) ; dossier : {'/'.join(chemin.split('/')[:-1])}"
                                         + ('' if date else ' ; date non lue (année du nom : %s)' % (annee_nom or 'inconnue'))
                                         + (' ; ' + ov['note'] if ov.get('note') else '')}],
            'source_page': [], 'document_organisme': [], 'document_norme': [], 'document_systeme': [], 'configuration': [],
            'performance': [], 'perf_feu': [], 'perf_effraction': [], 'perf_balistique': [], 'perf_aev': [], 'perf_acoustique': [],
            'perf_explosion': [], 'perf_mesure': [], 'cumul_performance': [], 'controle_humain': [],
        }
        if labo:
            doc['document_organisme'].append({'document_id': did, 'organisme_id': labo, 'role_code': 'laboratoire', 'nom_tel_qu_ecrit': None, 'source_page_id': None})

        def page_id(p):
            if not p:
                return None
            spid = f'SP-{did[4:]}-P{p}'
            if not any(s['id'] == spid for s in doc['source_page']):
                doc['source_page'].append({'id': spid, 'document_id': did, 'page_doc': p, 'page_doc_total': len(pages), 'section': None,
                                           'planche': None, 'type_zone_code': 'texte', 'libelle': None})
            return spid
        for k, sid in enumerate(sys_ids):
            doc['document_systeme'].append({'document_id': did, 'systeme_id': sid, 'role': 'principal' if k == 0 else 'variante', 'source_page_id': None})
        cfg = None
        if typo and sys_ids:
            cfg = f'CFG-{did[4:]}-1'
            doc['configuration'].append({'id': cfg, 'document_id': did, 'code': '1', 'libelle': nom[:120], 'typologie_code': typo,
                                         'systeme_id': sys_ids[0], 'nb_vantaux_min': None, 'nb_vantaux_max': None, 'vantaux_inegaux': None,
                                         'vitree': None, 'parent_configuration_id': None, 'source_page_id': None})
        norme_id = None
        if dom in NORMES:
            norme_id, code = NORMES[dom]
            normes_vues[norme_id] = code
            doc['document_norme'].append({'document_id': did, 'norme_id': norme_id, 'role': 'essai' if tdoc == 'rapport_essai' else 'reference',
                                          'paragraphe': None, 'source_page_id': None})
        global chemin_courant
        chemin_courant = chemin
        perfs = classes_domaine(dom, nom, pages) if dom and tdoc not in ('passeport_ce', 'synthese_fabricant') else []
        perfs = [dict(c, dom=dom) for c in perfs]
        # rapport combiné (ex. « RC4 + FB4 ») : la seconde classe est aussi enregistrée dans son propre domaine
        for d2, rx in (('effraction', r'(?<![A-Za-z])RC\s?[1-6]'), ('balistique', r'FB\s?[1-7]')):
            if dom in ('effraction', 'balistique') and d2 != dom and re.search(rx, nom):
                perfs += [dict(c, dom=d2) for c in classes_domaine(d2, nom, pages)]
        for j, c in enumerate(perfs, 1):
            pid = f'PERF-{did[4:]}-{j}'
            doc['performance'].append({'id': pid, 'document_id': did, 'configuration_id': cfg, 'domaine_code': c['dom'],
                                       'libelle_tel_qu_ecrit': c['libelle'][:120], 'classe_normalisee': c['classe'],
                                       'nature_code': 'classement' if tdoc in ('rapport_essai', 'rapport_classement', 'certificat', 'avis_expertise') else 'teste',
                                       'condition_texte': None if c['page'] else 'classe lue dans le nom de fichier, non retrouvée dans le texte',
                                       'source_page_id': page_id(c['page']), 'statut_extraction': c['statut']})
            t, row = perf_detail(c['dom'], pid, c['detail'], NORMES.get(c['dom'], (norme_id,))[0])
            doc[t].append(row)
            stats['perf'] += 1
        # Cumuls énoncés par le rapport lui-même
        feu = RE_FEU.search(nom) or (ov.get('feu') and re.search('.+', ov['feu']))  # classe feu explicite dans le nom uniquement
        autres = [p for p in perfs if p['dom'] == dom] if dom not in ('feu',) else []
        if feu and dom in ('effraction', 'balistique', 'explosion', 'acoustique') and autres:
            fx = feu.group(0)
            cf = re.sub(r'\s|-', '', fx).upper() if re.match(r'E', fx, re.I) else fx
            pf = find_page(pages[:3], r'E\s?I\s?[12]?\s?' + re.escape(re.sub(r'\D', '', fx)))
            for k, p in enumerate(autres, 1):
                doc['cumul_performance'].append({
                    'id': f'CUM-{did[4:]}-{k}', 'document_id': did, 'systeme_id': sys_ids[0] if sys_ids else None, 'typologie_code': typo,
                    'domaine_a': 'feu', 'classe_a': cf, 'domaine_b': dom, 'classe_b': p['classe'], 'statut_cumul': 'constate_rapport',
                    'condition_texte': f"Éprouvette décrite comme coupe-feu ({fx}) dans le nom du rapport ; classement feu = PV distinct",
                    'justificatifs': None, 'source_page_id': page_id(pf) if pf else None, 'statut_extraction': 'a_verifier'})
                stats['cumul'] += 1
        doms_nom = []
        if re.search(r'RC\s?[1-6]', nom) and re.search(r'FB\s?[1-7]', nom):
            rc = re.search(r'RC\s?([1-6])', nom).group(0).replace(' ', ''); fb = re.search(r'FB\s?[1-7]\s?N?S?', nom).group(0).replace(' ', '')
            doc['cumul_performance'].append({
                'id': f'CUM-{did[4:]}-RCFB', 'document_id': did, 'systeme_id': sys_ids[0] if sys_ids else None, 'typologie_code': typo,
                'domaine_a': 'effraction', 'classe_a': rc, 'domaine_b': 'balistique', 'classe_b': fb, 'statut_cumul': 'constate_rapport',
                'condition_texte': 'Les deux classes figurent dans le même rapport (nom de fichier) ; à confirmer dans le texte.',
                'justificatifs': None, 'source_page_id': page_id(find_page(pages, r'FB\s?[1-7]')), 'statut_extraction': 'a_verifier'})
            stats['cumul'] += 1
        doc['controle_humain'].append({'id': f'CTRL-{did[4:]}-AUTO', 'document_id': did, 'table_cible': 'document', 'ligne_id': did,
                                       'type_code': 'extraction_auto',
                                       'description': f"Rapport {num} ({dom or 'domaine ?'}) : métadonnées et classes extraites automatiquement "
                                                      f"({len(perfs)} performance(s)) — à relire.", 'statut': 'ouvert', 'resolution': None, 'source_page_id': None})
        if dom and not perfs and tdoc in ('rapport_essai', 'rapport_classement', 'certificat'):
            doc['controle_humain'].append({'id': f'CTRL-{did[4:]}-NT', 'document_id': did, 'table_cible': 'performance', 'ligne_id': None,
                                           'type_code': 'non_trouve', 'description': 'Aucune classe / valeur lue automatiquement : à saisir.',
                                           'statut': 'ouvert', 'resolution': None, 'source_page_id': None})
        doc = {k: v for k, v in doc.items() if v}
        json.dump(doc, open(os.path.join(OUT_DIR, f'RAP-{did[8:]}.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        stats['docs'] += 1
    cat = {
        'organisme': [{'id': oid, 'nom': n, 'nom_normalise': slug(n).replace('-', ' '), 'pays_code': p, 'ville': None, 'adresse': None,
                       'est_fabricant': 0, 'est_laboratoire': 1} for oid, (n, p) in sorted(labos_vus.items())],
        'norme': [{'id': nid, 'code': c, 'annee': None, 'amendement': None, 'titre': None} for nid, c in sorted(normes_vues.items())],
        'systeme': NOUVEAUX_SYSTEMES,
    }
    json.dump(cat, open(os.path.join(ROOT, 'data', 'sources', 'catalogue_rapports.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(stats)


if __name__ == '__main__':
    main()
