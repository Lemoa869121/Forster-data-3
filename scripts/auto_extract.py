#!/usr/bin/env python3
"""Extraction AUTOMATIQUE (texte natif + OCR) des PV -> data/sources/documents/AUTO-*.json + data/sources/catalogue_auto.json

Usage : python3 scripts/auto_extract.py <dossier_txt_ocr>
  Le dossier contient un .txt par PDF (pages séparées par \\f), nommé comme le PDF.
  Production : scripts/ocr_pdf.sh (pdftotext par page, tesseract fra 200 dpi pour les pages scannées).

Principes :
  * tout ce qui est extrait automatiquement porte statut_extraction = 'a_verifier' (ou 'ocr_degrade') ;
  * un controle_humain 'extraction_auto' par document ;
  * aucune donnée n'est déduite d'une ressemblance : seules les mentions présentes dans le texte sont enregistrées ;
  * les fichiers saisis manuellement (data/sources/documents/*.json sans préfixe AUTO-) sont ignorés ici et priment au build.
"""
import glob, json, os, re, sys, unicodedata
from collections import OrderedDict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib_sources import Catalogue, Fichier, norm_ref, slug  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'data', 'sources')

MOIS = {'janvier': 1, 'fevrier': 2, 'février': 2, 'mars': 3, 'avril': 4, 'mai': 5, 'juin': 6, 'juillet': 7, 'aout': 8, 'août': 8,
        'septembre': 9, 'octobre': 10, 'novembre': 11, 'decembre': 12, 'décembre': 12}
VERRIER = {'VETR': ('ORG-VETROTECH', 'VETROTECH SAINT-GOBAIN INTERNATIONAL AG'), 'PILK': ('ORG-PILKINGTON', 'PILKINGTON DEUTSCHLAND AG'),
           'PYRO': ('ORG-PYROGUARD', 'PYROGUARD UK LTD'), 'POLF': ('ORG-POLFLAM', 'POLFLAM SP. Z O.O.'),
           'AGC': ('ORG-AGC', 'AGC GLASS EUROPE'), 'GTRO': ('ORG-GLAS-TROESCH', 'GLAS TRÖSCH')}
ORG_PATTERNS = [('ORG-FORSTER', r'FORSTER'), ('ORG-VETROTECH', r'VETROTECH'), ('ORG-PILKINGTON', r'PILKINGTON'),
                ('ORG-PYROGUARD', r'PYROGUARD|C\.?G\.?I\.? INTERNATIONAL'), ('ORG-POLFLAM', r'POLFLAM'), ('ORG-AGC', r'\bAGC\b'),
                ('ORG-GLAS-TROESCH', r'GLAS\s*TR[OÖ]E?SCH|GLASTR[OÖ]SCH')]
SYSTEMES = [(r'PRESTO\s*XS', 'SYS-PRESTO-XS', 'Presto XS', 0, None), (r'PRESTO\s*60', 'SYS-PRESTO-60', 'Presto 60', 0, 60),
            (r'PRESTO(\s*50)?', 'SYS-PRESTO-50', 'Presto 50', 0, 50), (r'UNICO\s*XS', 'SYS-UNICO-XS', 'Unico XS', None, None),
            (r'UNICO', 'SYS-UNICO', 'Unico', None, None), (r'THERMFIX\s*LIGHT', 'SYS-THERMFIX-LIGHT', 'Thermfix Light', None, None),
            (r'THERMFIX\s*VARIO', 'SYS-THERMFIX-VARIO', 'Thermfix Vario', None, None),
            (r'FUEGO\s*LIGHT\s*120', 'SYS-FUEGO-LIGHT-120', 'Fuego Light 120', 1, None), (r'FUEGO\s*LIGHT\s*90', 'SYS-FUEGO-LIGHT-90', 'Fuego Light 90', 1, None),
            (r'FUEGO\s*LIGHT\s*60', 'SYS-FUEGO-LIGHT-60', 'Fuego Light 60', 1, None), (r'FUEGO\s*LIGHT\s*30', 'SYS-FUEGO-LIGHT-30', 'Fuego Light 30', 1, 65),
            (r'FUEGO\s*LIGHT', 'SYS-FUEGO-LIGHT', 'Fuego Light (série non précisée)', 1, None)]
GAMMES_VITRAGE = r'(PYROSWISS|CONTRAFLAM(?:\s+LITE|\s+STRUCTURE)?|PYROSTOP|PYRODUR|PYROGUARD|PYROBELITE|PYROBEL|POLFLAM|FIREFLAM|SWISSFLAM|VETROFLAM|PYRANOVA|FIRESWISS|PYRAN)'
KEYCAT = [(r'paumelle', 'paumelle', 'articulation'), (r'pion', 'pion_anti_degondage', 'articulation'), (r'pivot', 'pivot_sol', 'articulation'),
          (r'ferme[- ]porte|groom', 'ferme_porte', 'fermeture'), (r's[ée]lecteur', 'selecteur_fermeture', 'selecteur'),
          (r'g[âa]che', 'gache', 'condamnation'), (r'cr[ée]mone', 'cremone', 'condamnation'), (r'verrou', 'verrou', 'condamnation'),
          (r'serrure|coffre|p[êe]ne', 'serrure', 'condamnation'), (r'push[- ]?bar|anti[- ]?panique|b[ée]quille|poign', 'barre_antipanique', 'manoeuvre'),
          (r'ventouse|contr[ôo]le d.acc|lecteur', 'ventouse', 'controle_acces'), (r'parclose', 'parclose', 'maintien_remplissage'),
          (r'vis[- ]bouton|bouton', 'vis_bouton', 'maintien_remplissage'), (r'ressort', 'ressort_parclose', 'maintien_remplissage'),
          (r'epdm', 'joint_epdm', 'maintien_remplissage'), (r'fibre', 'bande_fibre', 'maintien_remplissage'),
          (r'intumescent|palusol|kerafix|palstop', 'joint_intumescent', 'etancheite'), (r'but[ée]e', 'joint_butee', 'etancheite'),
          (r'busette|douille|drainage', 'busette', 'drainage'), (r'seuil', 'seuil_automatique', 'accessoire'),
          (r'profil|montant|traverse|dormant|ouvrant|huisserie', 'profile', 'ossature_cloison')]
ROLE_OF = {'paumelle': 'articulation', 'pion_anti_degondage': 'articulation', 'pivot_sol': 'articulation', 'ferme_porte': 'fermeture',
           'selecteur_fermeture': 'selecteur', 'gache': 'condamnation', 'cremone': 'condamnation', 'verrou': 'condamnation', 'serrure': 'condamnation',
           'barre_antipanique': 'manoeuvre', 'ventouse': 'controle_acces', 'parclose': 'maintien_remplissage', 'vis_bouton': 'maintien_remplissage',
           'ressort_parclose': 'maintien_remplissage', 'joint_epdm': 'maintien_remplissage', 'bande_fibre': 'maintien_remplissage',
           'joint_intumescent': 'etancheite', 'joint_butee': 'etancheite', 'busette': 'drainage', 'seuil_automatique': 'accessoire',
           'profile': 'ossature_cloison', 'accessoire': 'accessoire', 'ouvre_porte': 'fermeture'}
TIERS = [(r'\b(TS\s?\d{2,4}(?:\s?FL|\s?WOOD)?)\b', 'ORG-DORMA', 'ferme_porte'), (r'\b(ITS\s?96(?:\s?2S)?)\b', 'ORG-DORMA', 'ferme_porte'),
         (r'\b(ED\s?(?:100|200|250))\b', 'ORG-DORMA', 'ouvre_porte'), (r'\b(HZ\s?[34]3\s?-?\s?F\d{0,2})\b', 'ORG-DORMA', 'verrou'),
         (r'\b(BTS\s?\d{2}\s?[A-Z]{0,3})\b', 'ORG-DORMA', 'pivot_sol'), (r'\b(TV\s?[12]00)\b', 'ORG-DORMA', 'ventouse'),
         (r'\b(STADI\s?BS)\b', 'ORG-ATHMER', 'seuil_automatique')]
RE_FORSTER = re.compile(r'(?<![\d.,])(9[0-9]{2}[ .]?[0-9]{3})(?![\d.,]|\s?mm)')
RE_PROFIL = re.compile(r'(?<![\d.,])((?:0[12]|3[0-9]|7[0-9]|7[0-9]{2})\.\d{3}(?:/T)?)(?![\d.,]|\s?(?:mm|m²|kg))')
RE_DATE = re.compile(r'\b(\d{1,2})(?:er)?\s+(janvier|f[ée]vrier|mars|avril|mai|juin|juillet|ao[uû]t|septembre|octobre|novembre|d[ée]cembre)\s+(\d{4})', re.I)
RE_CLASSE = re.compile(r'\b(E\s?[Il|]\s?[12]?|E\s?W|E)\s{0,3}(15|20|30|45|60|90|120|180|240)\b')


def strip(s):
    return ''.join(c for c in unicodedata.normalize('NFKD', s) if not unicodedata.combining(c))


def iso(m):
    d, mo, y = m.group(1), strip(m.group(2).lower()), m.group(3)
    return f'{int(y):04d}-{MOIS[mo]:02d}-{int(d):02d}'


def parse_filename(name):
    base = re.sub(r'\.pdf$', '', name)
    b = re.sub(r'^FR\s+', '', base)
    out = {'base': base}
    if b.startswith('SA '):
        parts = [p.strip() for p in re.split(r'\s+-\s+', b)]
        date = None
        if re.match(r'\d{2}-\d{2}-\d{4}$', parts[-1]):
            d_ = parts.pop(); date = f'{d_[6:]}-{d_[3:5]}-{d_[:2]}'
        parts = [p for p in parts if p != 'DAS CNPP']
        classes = ' '.join(p for p in parts[1:] if re.match(r'^E[IW]?\d', p))
        desc = ' '.join(p for p in parts[1:] if not re.match(r'^E[IW]?\d', p))
        out.update(numero=parts[0], classes=classes, desc=desc, verrier=None, marche='DAS CNPP', validite=date, das=True, note=None)
        return out
    parts = [p.strip() for p in re.split(r'\s+-\s*', b)]
    out['numero'] = parts[0]
    out['verrier'] = parts[1] if len(parts) > 4 and parts[1] in VERRIER else None
    rest = parts[2:] if out['verrier'] else parts[1:]
    out['desc'] = rest[0]
    out['marche'] = rest[1] if len(rest) > 1 else None
    dm = re.search(r'(\d{2})-(\d{2})-(\d{2,4})', ' '.join(rest[2:]) if len(rest) > 2 else '')
    if dm:
        y = dm.group(3); y = '20' + y if len(y) == 2 else y
        out['validite'] = f'{y}-{dm.group(2)}-{dm.group(1)}'
    out['note'] = re.search(r'\(([^)]*)\)\s*$', b).group(1) if re.search(r'\(([^)]*)\)\s*$', b) else None
    out['classes'] = ' '.join(re.findall(r'\bE[IW]?\d{2,3}\b', out['desc']))
    out['das'] = False
    return out


def typologie(desc):
    d = strip(desc.lower())
    if 'plancher' in d: return 'plancher_vitre'
    if 'verriere' in d: return 'verriere'
    if 'facade' in d: return 'facade_vitree'
    if 'bab' in d: return 'cloison_vitree_bord_a_bord'
    if 'porte' in d: return 'bloc_porte'
    if 'fenetre' in d and 'cloison' not in d: return 'fenetre'
    if 'ferme-porte' in d or 'operateur' in d: return 'bloc_porte'
    return 'cloison_vitree'


def norm_num(n):
    n = re.sub(r'\s*-\s*', '-', n.strip()).upper().replace(' ', '')
    return n


def find_systems(text):
    found = []
    T = strip(text.upper())
    for pat, sid, nom, iso_, prof in SYSTEMES:
        if re.search(pat, T):
            if sid == 'SYS-FUEGO-LIGHT' and any(s.startswith('SYS-FUEGO-LIGHT-') for s in found): continue
            if sid == 'SYS-PRESTO-50' and not re.search(r'PRESTO(?!\s*(XS|60))', T): continue
            if sid == 'SYS-UNICO' and not re.search(r'UNICO(?!\s*XS)', T): continue
            found.append(sid)
    return found


def segment(pages):
    """Découpe le fichier en documents logiques. Renvoie [(type, numero_brut, i_debut, i_fin)]."""
    starts = []
    for i, p in enumerate(pages):
        head = strip(p[:2500]).upper()
        head1 = re.sub(r'\s+', ' ', head)
        pn = re.search(r'PAGE\s*:?\s*(\d{1,3})\s*(?:/|SUR)\s*\d+', head1)
        first = pn is not None and pn.group(1) == '1'
        cont = pn is not None and pn.group(1) != '1'
        if re.search(r'RECONDUCTION\s+N\s*[°O]\s*([\d]+\s*/\s*\d+)', head1) and not cont and (first or i == 0 or 'DU PROCES-VERBAL' in head1):
            m = re.search(r'RECONDUCTION\s+N\s*[°O]\s*([\d]+\s*/\s*\d+)', head1)
            starts.append((i, 'reconduction', m.group(1).replace(' ', '')))
        elif re.search(r'EXTENSION (?:DE )?CLASSEMENT', head1) and not cont and (first or re.search(r'OBJET DE L.EXTENSION', head1)):
            multi = 'MULTIPLE' in head1
            m = re.search(r'EXTENSION DE CLASSEMENT\s+N\s*[°O]?\s*(?:SUR LE PROCES-VERBAL N\s*[°O]?)?\s*[▪•]?\s*([A-Z0-9/\-]+)', head1)
            starts.append((i, 'extension_multiple' if multi else 'extension', m.group(1) if m else None))
        elif re.search(r'PROCES[- ]VERBAL DE CLASSEMENT\s*N\s*[°O]', head1) and not cont and (first or i == 0 or re.search(r'CONCERNANT|DEMANDEUR|CE PROCES-VERBAL COMPORTE', head1)):
            m = re.search(r'PROCES[- ]VERBAL DE CLASSEMENT\s*N\s*[°O]\s*([A-Z0-9][A-Z0-9 \-]{3,20})', head1)
            starts.append((i, 'pv_classement', m.group(1).strip() if m else None))
        elif re.search(r'PROCES[- ]VERBAL\s+N\s*[°O]\s*SA', head1) or re.search(r'CNPP', head1) and i == 0:
            starts.append((i, 'pv_das', None))
    # dédoublonner les débuts consécutifs de même type (pages de garde multiples)
    clean = []
    for s in starts:
        if clean and s[1] == clean[-1][1] and s[0] - clean[-1][0] <= 1 and s[1] != 'reconduction':
            continue
        clean.append(s)
    if not clean or clean[0][0] != 0:
        clean.insert(0, (0, 'pv_classement', None))
    segs = []
    for k, (i, t, n) in enumerate(clean):
        j = clean[k + 1][0] if k + 1 < len(clean) else len(pages)
        segs.append((t, n, i, j))
    return segs


def ctx(text, a, b, w=90):
    s = text[max(0, a - w):b + w]
    s = re.sub(r'\s+', ' ', s).strip()
    return s[:200]


def guess_cat(context, ref):
    c = strip(context.lower())
    best = None; bestpos = 10 ** 6
    r0 = c.find(strip(ref.lower()).replace(' ', '')[:3])
    for pat, cat, role in KEYCAT:
        for m in re.finditer(pat, c):
            dpos = abs(m.start() - (r0 if r0 >= 0 else len(c) // 2))
            if dpos < bestpos:
                best, bestpos = cat, dpos
    rn = norm_ref(ref)
    if re.match(r'^\d{2,3}\d{3}(/T)?$', rn) and '.' in ref: return 'profile'
    if rn.startswith('901'): return 'parclose'
    if rn == '905307': return 'joint_butee'
    if rn.startswith('905'): return 'joint_epdm'
    if rn in ('906577', '906578', '906579', '906574'): return 'vis_bouton'
    if rn == '906421': return 'ressort_parclose'
    if rn in ('900100', '980101'): return 'busette'
    if rn.startswith('948') and best not in ('bande_fibre', 'joint_intumescent'): return 'joint_intumescent'
    return best or 'accessoire'


def extract_file(cat, path, existing_doc_ids):
    name = os.path.basename(path)[:-4] + '.pdf'
    fn = parse_filename(name)
    pages = open(path, encoding='utf-8', errors='replace').read().split('\f')
    if pages and not pages[-1].strip(): pages = pages[:-1]
    fid = 'FIC-AUTO-' + slug(norm_num(fn['numero']))
    F = Fichier(cat, fid, nom_fichier=name, drive_file_id=None, url=None, taille_octets=None, date_modification=None,
                code_fournisseur_vitrage=fn.get('verrier'), code_marche=fn.get('marche'),
                commentaire='Extraction automatique (texte natif + OCR tesseract) — ' + (fn.get('note') or 'relecture requise'))
    pv_num = norm_num(fn['numero']) if not fn['das'] else fn['numero']
    pv_id = 'DOC-' + slug(pv_num) if not fn['das'] else 'DOC-' + slug(fn['numero'])
    segs = segment(pages) if not fn['das'] else [('pv_das', fn['numero'], 0, len(pages))]
    typo = typologie(fn['desc'])
    verr = VERRIER.get(fn.get('verrier') or '', (None, None))[0]
    labo = 'ORG-CNPP' if fn['das'] else 'ORG-EFECTIS-FRANCE'
    full = '\f'.join(pages)
    seen_doc = set()
    ordre = 0
    pv_present = False
    for (t, nbrut, i0, i1) in segs:
        ordre += 1
        seg_pages = pages[i0:i1]
        txt = '\n'.join(seg_pages)
        T1 = re.sub(r'\s+', ' ', strip(txt))
        if t == 'pv_classement' or t == 'pv_das':
            did, numero, nn = pv_id, fn['numero'], pv_num
            rev = None
            mr = re.search(r'R[ée]vision\s+(\d+)', ' '.join(seg_pages[:2]))
            if mr: rev = mr.group(1)
            if did in seen_doc:
                did = f'{pv_id}-PART{ordre}'; nn = f'{pv_num}/PART{ordre}'
            pv_present = pv_present or did == pv_id
        elif t == 'reconduction':
            n = (nbrut or f'R{ordre}').replace('/', '-')
            did, numero, nn, rev = f'{pv_id}-REC-{n}', nbrut or '?', f'{pv_num}/REC-{nbrut or ordre}', None
        else:
            h = strip(' '.join(seg_pages[:1]))[:3000]
            efr = [x for x in re.findall(r'\bEFR-\d{2}-\d{6}\b', h) if x != pv_num]
            sl = re.findall(r'(?<![\d/])(\d{2}/\d{1,2})(?![\d/])', h)
            if 'MULTIPLE' in h.upper() and efr: n = efr[0]
            elif sl: n = sl[0]
            elif efr: n = efr[0]
            else: n = f'X{ordre}'
            if re.match(r'^(EFR|\d{2}-[A-Z]-)', n):
                did, nn = 'DOC-' + slug(n), n
            else:
                did, nn = f'{pv_id}-EXT-{n.replace("/", "-")}', f'{pv_num}/EXT-{n}'
            numero, rev = n, None
        if did in seen_doc:
            did += f'-{ordre}'; nn += f'-{ordre}'
        seen_doc.add(did)
        # dates
        emis = None
        for m in RE_DATE.finditer(txt):
            ctxs = txt[max(0, m.start() - 60):m.start()]
            if re.search(r'\ble\s*$', ctxs) or re.search(r'Fait\s', ctxs):
                emis = iso(m)
        valid = None
        mv = re.search(r"jusqu.au\s*:?\s*" + RE_DATE.pattern, txt, re.I)
        if mv:
            valid = f'{int(mv.group(3)):04d}-{MOIS[strip(mv.group(2).lower())]:02d}-{int(mv.group(1)):02d}'
        else:
            mv = re.search(r"jusqu.au\s*:?\s*(.{0,60})", txt, re.I | re.S)
        if t == 'pv_das' and not valid and fn.get('validite'):
            valid = fn['validite']
        objet = None
        mo = re.search(r'Concernant\s*:?\s*(.{10,220}?)(?:\n\s*\n|Ossature|Demandeur)', txt, re.S)
        if mo: objet = re.sub(r'\s+', ' ', mo.group(1)).strip()
        if t.startswith('extension'):
            mo = re.search(r"Objet de l.extension\s*(.{5,300}?)(?:\n\s*\n|Dur[ée]e de validit)", txt, re.S)
            if mo: objet = re.sub(r'\s+', ' ', mo.group(1)).strip()
        typ = t if t != 'pv_das' else 'pv_das'
        F.doc(did, numero, nn, typ, revision=rev, ordre=ordre, emission=emis,
              validite=None if t.startswith('extension') else valid, lie_pv=1 if t.startswith('extension') else 0,
              pages=len(seg_pages), labo=labo, objet=objet or (fn['desc'] if did == pv_id else None), statut='a_verifier',
              com='Extraction automatique — relecture requise')
        F.ctrl(did, 'extraction_auto', f'Document extrait automatiquement (OCR) : pages PDF {i0 + 1}-{i1} de « {name} ». Relire classement, dates, composants et dimensions.')
        sp0 = F.page(did, 1, len(seg_pages), None, None, 'page_garde', f'page PDF {i0 + 1}')
        F.org(did, labo, 'laboratoire', page=sp0)
        head = strip(' '.join(seg_pages[:2])).upper()
        for oid, pat in ORG_PATTERNS:
            if re.search(pat, head):
                F.org(did, oid, 'demandeur', page=sp0)
        # relations
        if t == 'reconduction':
            F.rel(did, pv_id, 'reconduit', emis, page=sp0)
            mr = re.search(r'sont reconduites\s*:\s*(.{0,200}?)(?:\n\s*\n|L.extension|Dur[ée]e|$)', txt, re.S)
            if mr:
                for e in re.findall(r'\b(\d{2}/\d{1,2}|EFR-\d{2}-\d{6})\b', mr.group(1)):
                    tid = 'DOC-' + slug(e) if e.startswith('EFR') else f'{pv_id}-EXT-{e.replace("/", "-")}'
                    F.rel(did, tid, 'reconduit_extension', page=sp0)
                    existing_doc_ids.setdefault(tid, (e if e.startswith('EFR') else f'{pv_num}/EXT-{e}', e, pv_id))
            for e in re.findall(r"extension\s+(\d{2}/\d{1,2})\s+n.est pas reconduite", strip(txt), re.I):
                tid = f'{pv_id}-EXT-{e.replace("/", "-")}'
                F.rel(did, tid, 'non_reconduit', page=sp0)
                existing_doc_ids.setdefault(tid, (f'{pv_num}/EXT-{e}', e, pv_id))
        elif t.startswith('extension'):
            targets = set(re.findall(r'\b(\d{2}\s?-\s?[AV]\s?-\s?\d{3,4}|EFR-\d{2}-\d{6})\b', strip(' '.join(seg_pages[:2]))))
            targets = {norm_num(x) for x in targets} or {pv_num}
            for x in targets:
                tid = 'DOC-' + slug(x)
                if tid == did: continue
                F.rel(did, tid, 'etend', emis, page=sp0)
                if tid != pv_id: existing_doc_ids.setdefault(tid, (x, x, None))
            for e in re.findall(r"n.est pas cumulable avec (?:l.extension\s*)?(\d{2}/\d{1,2}|EFR-\d{2}-\d{6})", strip(txt), re.I):
                tid = 'DOC-' + slug(e) if e.startswith('EFR') else f'{pv_id}-EXT-{e.replace("/", "-")}'
                if tid != did:
                    F.rel(did, tid, 'non_cumulable_avec', page=sp0)
                    existing_doc_ids.setdefault(tid, (e if e.startswith('EFR') else f'{pv_num}/EXT-{e}', e, pv_id))
        if t in ('pv_classement', 'pv_das') and did != pv_id:
            F.rel(did, pv_id, 'annexe_de', page=sp0)
        # normes
        for m in set(re.findall(r'\b(EN\s?13501-2|EN\s?1634-1|EN\s?1364-[1-4]|NF\s?S\s?61-9\d\d|EN\s?1154|EN\s?1155|EN\s?1125|EN\s?179)\s*(?:[:\-]\s*((?:19|20)\d{2}))?', txt)):
            code = re.sub(r'\s+', ' ', m[0]).replace('EN1', 'EN 1').replace('NFS', 'NF S').strip()
            code = re.sub(r'^EN(\d)', r'EN \1', code)
            nid = cat.norme(code, m[1] or None)
            role = 'classement' if '13501' in code else 'reference'
            F.t['document_norme'] = [r for r in F.t['document_norme'] if not (r['document_id'] == did and r['norme_id'] == nid and r['role'] == role)]
            F.norme(did, nid, role, page=sp0)
        # essais cités (phrases contenant « essai »)
        for m in re.finditer(r"essai[^.]{0,160}?\b(EFR-\d{2}-\d{6}(?:-[A-Z])?|\d{2}-[GVA]-\d{3,4}|DMT-[A-Z0-9-]{4,})\b", txt, re.I):
            ref = m.group(1)
            if ref in (fn['numero'],): continue
            eid = cat.essai(ref)
            if not any(r['essai_id'] == eid and r['document_id'] == did for r in F.t['document_essai']):
                F.essai(did, eid, 'reference', page=sp0)
        # systèmes
        sysids = find_systems(fn['desc'] + ' ' + ' '.join(seg_pages[:3]))
        for sid in sysids:
            for pat, s2, nom, iso_, prof in SYSTEMES:
                if s2 == sid: cat.sys(sid, nom, 'ORG-FORSTER', iso_, prof)
            F.sysdoc(did, sid, 'principal' if sid == (sysids[0] if sysids else None) else 'variante', sp0)
        # configuration + performances
        cfg = None
        if t in ('pv_classement', 'pv_das') or t.startswith('extension'):
            cfg = F.config(did, 'AUTO', (fn['desc'] if did == pv_id else (objet or 'Variante'))[:200], typo, sysids[0] if sysids else None, vitree=1)
        if t in ('pv_classement',) or t.startswith('extension'):
            # bloc classement : ancré sur « combinaisons suivantes » (PV) ou sur l'en-tête « R E I W » des conclusions (extensions)
            U = strip(txt)
            zones = []
            for m in re.finditer(r"(?i)combinaisons suivantes|l.element est classe", U):
                z = U[m.end():m.end() + 600]
                z = re.split(r"(?i)Les portes qui|CONDITIONS DE VALIDIT|\n\s*4[.\s]|Aucune modification", z)[0]
                zones.append(z)
            if t.startswith('extension'):
                for m in re.finditer(r"R\s{0,3}E\s{0,3}[I!l|]\s{0,3}W", U):
                    zones.append(U[m.end():m.end() + 160])
            classes = OrderedDict()
            for zone in zones:
                for m in RE_CLASSE.finditer(zone):
                    k = re.sub(r'[l|]', 'I', re.sub(r'\s', '', m.group(1))) + ' ' + m.group(2)
                    classes[k] = m.group(0)
            fclasses = []
            if did == pv_id and fn.get('classes'):
                for c in fn['classes'].split():
                    mm = re.match(r'(E[IW]?)(\d+)', c)
                    fclasses.append(mm.group(1) + ' ' + mm.group(2))
            for k, ecrit in classes.items():
                lettres, dur = k.split(' ')
                i = 'I' in lettres; w = 'W' in lettres; vi = None
                if i: vi = 'I2' if lettres.endswith('2') else ('I1' if lettres.endswith('1') else 'I')
                F.perf_feu(did, cfg, ecrit, k if not vi or vi == 'I' else f'EI{vi[1]} {dur}', int(dur), i=int(i), vi=vi, w=int(w),
                           page=sp0, statut='a_verifier', cond='Lecture automatique (OCR) du tableau de classement')
            manquants = [c for c in fclasses if c.replace('EI2', 'EI') not in [k.replace('EI2', 'EI') for k in classes]]
            for c in manquants:
                lettres, dur = c.split(' ')
                F.perf_feu(did, cfg, c + ' (nom de fichier)', c, int(dur), i=int('I' in lettres), vi='I' if 'I' in lettres else None, w=int('W' in lettres),
                           page=sp0, statut='non_trouve', cond='Classe annoncée par le nom de fichier, non lue dans le tableau OCR')
            if manquants:
                F.ctrl(did, 'non_trouve', 'Classe(s) ' + ', '.join(manquants) + ' du nom de fichier non retrouvée(s) dans le tableau de classement OCR : vérifier sur l\'original.')
        # sens du feu / interdictions
        ms = re.search(r'SENS D[EU] FEU\s*:?\s*(.{5,400}?)(?:\n\s*\n\s*\d|\n[A-Z0-9][^\n]{0,40}VALIDIT|$)', txt, re.S | re.I)
        if ms:
            s = re.sub(r'\s+', ' ', ms.group(1)).strip()[:400]
            F.restr(did, 'sens_feu', s[:160], s, cfg, page=sp0)
        if re.search(r'Aucun autre classement', txt, re.I):
            F.restr(did, 'interdiction', 'Aucun autre classement n\'est autorisé', None, cfg, page=sp0)
        if re.search(r'all[èe]ge n.est pas autoris|sur all[èe]ge n.est pas', txt, re.I):
            F.restr(did, 'interdiction', 'Montage sur allège non autorisé (selon texte)', None, cfg, page=sp0)
        if re.search(r'n.est pas cumulable', txt, re.I):
            m = re.search(r'([^.]{0,120}n.est pas cumulable[^.]{0,160})', txt, re.I)
            F.restr(did, 'cumul_extensions', re.sub(r'\s+', ' ', m.group(1)).strip()[:200], None, cfg, page=sp0)
        # vitrages
        seenv = set()
        for k, p in enumerate(seg_pages):
            P = strip(p)
            for m in re.finditer(GAMMES_VITRAGE + r'[\s®]*([A-Z]{0,4}\s?)?(\d{2,3}(?:\s?[-/]\s?\d{1,4})?)?(\s?(?:CLIMAPLUS|CLIMALIT|DGU|ISOLANT|STADIP|CORNER|VISI|XS)?)', P, re.I):
                g = re.sub(r'\s+', ' ', m.group(1).upper())
                rest = ' '.join(x for x in [(m.group(2) or '').strip(), (m.group(3) or '').replace(' ', ''), (m.group(4) or '').strip()] if x)
                des = (g + ' ' + rest).strip().upper()
                if des in seenv or len(seenv) > 40: continue
                seenv.add(des)
                typv = 'isolant' if re.search(r'CLIMAPLUS|CLIMALIT|DGU|ISOLANT', des) else ('feuillete' if 'STADIP' in des else 'monolithique')
                sp = F.page(did, k + 1, len(seg_pages), None, None, 'texte', f'page PDF {i0 + k + 1}')
                F.comp(did, des, verr if g not in ('VETROFLAM',) else 'ORG-VETROTECH', 'vitrage', 'remplissage', ctx(P, m.start(), m.end()),
                       cfg, None, page=sp, xstat='a_verifier',
                       typed=('dc_vitrage', dict(gamme=g, designation=des, type_vitrage_code=typv, epaisseur_mm=None, epaisseur_min_mm=None, epaisseur_max_mm=None,
                                                 classe_nominale=None, intercalaire_min_mm=None, intercalaire_max_mm=None, composition_detaillee_disponible=None)))
        # composants Forster et tiers
        seenr = set()
        for k, p in enumerate(seg_pages):
            P = p
            sp = None
            cands = [(m.group(1), m.start(), m.end(), 'ORG-FORSTER', None) for m in RE_FORSTER.finditer(P)] + \
                    [(m.group(1), m.start(), m.end(), 'ORG-FORSTER', 'profile') for m in RE_PROFIL.finditer(P)]
            for pat, fab, c0 in TIERS:
                cands += [(m.group(1), m.start(), m.end(), fab, c0) for m in re.finditer(pat, P)]
            for ref, a, b, fab, c0 in cands:
                rn = norm_ref(ref)
                if (fab, rn) in seenr: continue
                if fab == 'ORG-FORSTER' and c0 is None and not rn.startswith(('90', '91', '92', '93', '94', '95', '96', '97', '98')):
                    continue
                seenr.add((fab, rn))
                c = ctx(P, a, b)
                catg = c0 or guess_cat(c, ref)
                if catg == 'ouvre_porte': role = 'fermeture'
                else: role = ROLE_OF.get(catg, 'accessoire')
                if sp is None:
                    pl = re.search(r'Planche\s*(?:n\s*[°o]\s*)?(\d{1,3})', P, re.I)
                    sp = F.page(did, k + 1, len(seg_pages), None, f'Planche {pl.group(1)}' if pl else None,
                                'planche' if pl else 'texte', f'page PDF {i0 + k + 1}')
                F.comp(did, ref.replace(' ', '') if fab == 'ORG-FORSTER' and re.match(r'9\d\d \d{3}', ref) else ref, fab, catg, role, c, cfg, None,
                       page=sp, xstat='a_verifier', brute=ref)
        # dimensions simples : « hauteur/largeur maximale ... : NNNN mm »
        for k, p in enumerate(seg_pages):
            for m in re.finditer(r"(Hauteur|Largeur|Surface)\s+maximale\s+([^:\n]{0,120}?)\s*:\s*(\d[\d\s.,]{1,8})\s*(mm|m²|m2)", p, re.I):
                g = strip(m.group(1).lower()); lib = re.sub(r'\s+', ' ', m.group(0))[:200]
                lw = strip(lib.lower())
                obj = 'imposte' if 'imposte' in lw else 'allege' if 'allege' in lw else 'ensemble' if 'ensemble' in lw else \
                      'facade_entre_dalles' if 'dalle' in lw else 'vantail_hors_tout' if 'vantail' in lw else 'passage_libre' if 'passage' in lw else \
                      'vitrage_hors_tout' if 'vitrage' in lw else 'panneau' if 'panneau' in lw else 'cloison'
                val = m.group(3).replace(' ', '').replace(',', '.')
                if val.count('.') > 1 or not re.match(r'^\d+(\.\d+)?$', val): continue
                sp = F.page(did, k + 1, len(seg_pages), None, None, 'texte', f'page PDF {i0 + k + 1}')
                F.fmt(did, obj, lib, [(g, 'autorise_max', 'le', val, m.group(4).replace('m2', 'm²'))], cfg, page=sp, statut='a_verifier')
        # supports
        for pat, typ_s in [(r'b[ée]ton arm[ée]', 'beton_arme'), (r'b[ée]ton cellulaire', 'beton_cellulaire'), (r'parpaing|b[ée]ton plein', 'beton_plein_parpaing'),
                           (r'98\s*/\s*48', 'cloison_legere_98_48'), (r'120\s*/\s*70', 'cloison_legere_120_70')]:
            m = re.search(pat, txt, re.I)
            if m and t in ('pv_classement',):
                mv2 = re.search(r'(\d{3,4})\s*kg/m', txt[m.start():m.start() + 200])
                F.support(did, typ_s, cfg, float(mv2.group(1)) if mv2 and 'cloison' not in typ_s else None, 'ge' if mv2 and 'cloison' not in typ_s else None,
                          cond='Mention détectée automatiquement : ' + ctx(txt, m.start(), m.end()), page=sp0)
    return F, pv_present, pv_id, pv_num, fn


def main():
    txtdir = sys.argv[1]
    cat = Catalogue()
    # catalogue manuel (pour réutiliser les mêmes identifiants) + entités nouvelles
    man = json.load(open(os.path.join(SRC, 'catalogue.json'), encoding='utf-8'))
    man_ids = {t: {r.get('id') for r in rows if r.get('id')} for t, rows in man.items()}
    for r in man.get('reference_composant', []):
        cat.t['reference_composant'][(r['fabricant_id'], r['reference_normalisee'])] = r
    cat.org('ORG-AGC', 'AGC GLASS EUROPE', 'BE', None, fab=1)
    cat.org('ORG-GLAS-TROESCH', 'GLAS TRÖSCH', 'CH', None, fab=1)
    cat.org('ORG-CNPP', 'CNPP', 'FR', 'Vernon', labo=1)
    for o in ['ORG-EFECTIS-FRANCE', 'ORG-FORSTER', 'ORG-VETROTECH', 'ORG-PILKINGTON', 'ORG-PYROGUARD', 'ORG-POLFLAM', 'ORG-DORMA', 'ORG-ATHMER']:
        cat.t['organisme'][o] = {'id': o}
    manual_files = {os.path.basename(p) for p in glob.glob(os.path.join(SRC, 'documents', '*.json')) if not os.path.basename(p).startswith('AUTO-')}
    manual_pvs = {'11-A-507', '13-A-175', '08-A-275', '13-A-704', 'EFR-21-002687', 'EFR-24-000553'}
    for p in glob.glob(os.path.join(SRC, 'documents', 'AUTO-*.json')):
        os.remove(p)
    stubs = {}
    done = []
    for path in sorted(glob.glob(os.path.join(txtdir, '*.txt'))):
        fn = parse_filename(os.path.basename(path)[:-4] + '.pdf')
        if norm_num(fn['numero']) in manual_pvs:
            continue
        F, present, pv_id, pv_num, fn = extract_file(cat, path, stubs)
        done.append((F, pv_id))
    # documents cités non fournis (extensions reconduites absentes, PV visés) : stubs
    all_ids = set()
    for F, _ in done:
        all_ids |= {d['id'] for d in F.t['document']}
    manual_doc_ids = set()
    for fname in manual_files:
        manual_doc_ids |= {d['id'] for d in json.load(open(os.path.join(SRC, 'documents', fname), encoding='utf-8'))['document']}
    S = Fichier(cat, 'FIC-AUTO-CITES', nom_fichier='(documents cités non fournis — extraction automatique)', commentaire='Pseudo-fichier : documents référencés mais absents du corpus')
    S.t['fichier_source'] = []
    for tid, (nn, num, parent) in sorted(stubs.items()):
        if tid in all_ids or tid in manual_doc_ids: continue
        S.doc(tid, num, nn, 'extension' if '/EXT-' in nn else 'document_reference', present=0, statut='non_trouve', lie_pv=1 if '/EXT-' in nn else 0)
        if parent and '/EXT-' in nn:
            S.rel(tid, parent, 'etend')
    # relations pointant vers des documents inconnus -> stub
    known = all_ids | manual_doc_ids | {d['id'] for d in S.t['document']}
    for F, _ in done + [(S, None)]:
        for r in F.t['document_relation']:
            if r['document_cible_id'] not in known:
                cid = r['document_cible_id']
                S.doc(cid, cid[4:], cid[4:], 'document_reference', present=0, statut='non_trouve')
                known.add(cid)
    os.makedirs(os.path.join(SRC, 'documents'), exist_ok=True)
    for F, _ in done:
        F.dump(os.path.join(SRC, 'documents', 'AUTO-' + F.fid[9:] + '.json'))
    S.dump(os.path.join(SRC, 'documents', 'AUTO-ZZ-CITES.json'))
    # catalogue automatique : uniquement les lignes absentes du catalogue manuel
    out = OrderedDict()
    for t, rows in cat.t.items():
        keep = []
        for k, r in rows.items():
            if list(r.keys()) == ['id']: continue
            if r.get('id') and r['id'] in man_ids.get(t, set()): continue
            if t == 'reference_composant' and r in man.get('reference_composant', []): continue
            keep.append(r)
        out[t] = keep
    json.dump(out, open(os.path.join(SRC, 'catalogue_auto.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'{len(done)} fichiers extraits ; {len(S.t["document"])} documents cités ajoutés ; '
          f'{len(out["reference_composant"])} nouvelles références')


if __name__ == '__main__':
    main()
