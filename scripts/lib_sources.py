"""Bibliothèque de saisie : produit des lignes conformes au schéma (clés = colonnes)."""
import json, re, unicodedata, os
from collections import OrderedDict

def norm_txt(s):
    s = unicodedata.normalize('NFKD', s)
    s = ''.join(c for c in s if not unicodedata.combining(c))
    return s

def norm_ref(r):
    return re.sub(r'[\s\.]', '', r).upper()

def slug(s):
    s = norm_txt(s).upper()
    s = re.sub(r'[^A-Z0-9/+]+', '-', s).strip('-')
    return s.replace('/', '_').replace('+', 'P')

class Catalogue:
    def __init__(self):
        self.t = OrderedDict((k, OrderedDict()) for k in [
            'organisme','organisme_alias','intervenant','norme','systeme','essai','essai_resultat',
            'reference_composant','reference_alias','enrichissement_externe'])
    def add(self, table, row, key=None):
        key = key or row.get('id') or tuple(row.values())
        if key in self.t[table]:
            return self.t[table][key].get('id', key)
        self.t[table][key] = row
        return row.get('id', key)
    def org(self, oid, nom, pays=None, ville=None, fab=0, labo=0, adresse=None):
        return self.add('organisme', dict(id=oid, nom=nom, nom_normalise=norm_txt(nom).upper(), pays_code=pays,
                                          ville=ville, adresse=adresse, est_fabricant=fab, est_laboratoire=labo))
    def alias_org(self, oid, alias):
        self.add('organisme_alias', dict(organisme_id=oid, alias=alias), key=(oid, alias))
    def pers(self, nom):
        pid = 'PER-' + slug(nom)
        return self.add('intervenant', dict(id=pid, nom=nom))
    def norme(self, code, annee=None, amend=None, titre=None):
        nid = 'NRM-' + slug(code + ('-' + annee if annee else '') + (amend or ''))
        return self.add('norme', dict(id=nid, code=code, annee=annee, amendement=amend, titre=titre))
    def sys(self, sid, nom, fab, iso=None, prof=None, com=None):
        return self.add('systeme', dict(id=sid, nom=nom, nom_normalise=norm_txt(nom).upper(), fabricant_id=fab,
                                        isolation_thermique=iso, profondeur_mm=prof, commentaire=com))
    def essai(self, ref, labo=None, norme=None, date=None, objet=None, systeme=None):
        eid = 'ESS-' + slug(ref)
        return self.add('essai', dict(id=eid, reference=ref, laboratoire_id=labo, norme_id=norme,
                                      date_essai=date, objet=objet, systeme_teste=systeme))
    def resultat(self, eid, crit, duree, op='eq', cond=None, page=None):
        rid = f'{eid}-RES-{crit}-{len(self.t["essai_resultat"])+1:03d}'
        return self.add('essai_resultat', dict(id=rid, essai_id=eid, critere_code=crit, duree_min=duree,
                                               operateur_code=op, condition_essai=cond, nature_code='teste',
                                               source_page_id=page))
    def ref(self, reference_brute, fab, cat, desig=None):
        rn = norm_ref(reference_brute)
        fabslug = fab.replace('ORG-', '') if fab else 'INCONNU'
        rid = f'REF-{fabslug}-{slug(rn)}'
        key = (fab, rn)
        if key in self.t['reference_composant']:
            return self.t['reference_composant'][key]['id']
        self.t['reference_composant'][key] = dict(id=rid, reference_normalisee=rn, fabricant_id=fab,
                                                 categorie_code=cat, designation=desig)
        return rid
    def ref_alias(self, rid, alias, typ, doc=None):
        self.add('reference_alias', dict(reference_id=rid, alias=alias, type_alias=typ, document_id=doc), key=(rid, alias))
    def enrich(self, rid, carac, src, url, date, statut, txt=None, num=None, b=None, unite=None, com=None):
        eid = f'ENR-{len(self.t["enrichissement_externe"])+1:04d}'
        return self.add('enrichissement_externe', dict(id=eid, reference_id=rid, type_caracteristique_code=carac,
            valeur_texte=txt, valeur_num=num, valeur_bool=b, unite_code=unite, source='enrichissement',
            source_libelle=src, source_url=url, date_recherche=date, statut_fiabilite_code=statut, commentaire=com))
    def dump(self, path):
        out = OrderedDict((k, list(v.values())) for k, v in self.t.items())
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(out, f, ensure_ascii=False, indent=1)


TYPED = ['dc_profile','dc_vitrage','dc_serrure','dc_articulation','dc_ferme_porte','dc_joint','dc_fixation']

class Fichier:
    """Un fichier source (PDF) et tous ses documents logiques."""
    TABLES = ['fichier_source','document','source_page','document_relation','document_organisme',
              'document_signataire','document_norme','document_essai','document_systeme','configuration',
              'performance','perf_feu','document_composant','caracteristique_document'] + TYPED + \
             ['dimension_format','dimension','support_pose','restriction','controle_humain']
    def __init__(self, cat, fid, **kw):
        self.cat = cat
        self.fid = fid
        self.t = OrderedDict((k, []) for k in self.TABLES)
        self._sp = {}
        self._n = {}
        self.t['fichier_source'].append(dict(id=fid, **kw))
    def _id(self, prefix):
        self._n[prefix] = self._n.get(prefix, 0) + 1
        return f'{prefix}-{self._n[prefix]:04d}'
    def doc(self, did, numero, num_norm, typ, **kw):
        row = dict(id=did, numero=numero, numero_normalise=num_norm, revision=kw.pop('revision', None),
                   type_code=typ, domaine_code=kw.pop('domaine', 'feu'), objet=kw.pop('objet', None),
                   laboratoire_id=kw.pop('labo', 'ORG-EFECTIS-FRANCE'), date_emission=kw.pop('emission', None),
                   date_validite=kw.pop('validite', None), validite_liee_au_pv=kw.pop('lie_pv', 0),
                   nb_pages=kw.pop('pages', None), arrete_reference=kw.pop('arrete', None),
                   numeros_affaire=kw.pop('affaires', None),
                   fichier_source_id=kw.pop('fichier', self.fid), ordre_dans_fichier=kw.pop('ordre', None),
                   present_dans_corpus=kw.pop('present', 1), statut_extraction=kw.pop('statut', 'extrait'),
                   commentaire=kw.pop('com', None))
        assert not kw, kw
        if not row['present_dans_corpus']:
            row['fichier_source_id'] = None
        self.t['document'].append(row)
        return did
    def page(self, doc, p=None, tot=None, section=None, planche=None, zone='texte', lib=None):
        key = (doc, p, section, planche)
        if key in self._sp:
            return self._sp[key]
        sid = f'SP-{doc[4:]}-' + (f'P{p:03d}' if p is not None else 'PX') + \
              (f'-{slug(section)}' if section else '') + (f'-PL{slug(planche)}' if planche else '')
        self._sp[key] = sid
        self.t['source_page'].append(dict(id=sid, document_id=doc, page_doc=p, page_doc_total=tot, section=section,
                                          planche=planche, type_zone_code=zone, libelle=lib))
        return sid
    def rel(self, src, cible, typ, date=None, com=None, page=None):
        self.t['document_relation'].append(dict(id=f'REL-{src[4:]}-{typ}-{cible[4:]}', document_source_id=src,
            document_cible_id=cible, type_relation_code=typ, date_relation=date, commentaire=com, source_page_id=page))
    def org(self, doc, oid, role, nom=None, page=None):
        self.t['document_organisme'].append(dict(document_id=doc, organisme_id=oid, role_code=role,
                                                 nom_tel_qu_ecrit=nom, source_page_id=page))
    def sign(self, doc, nom, fonction=None):
        self.t['document_signataire'].append(dict(document_id=doc, intervenant_id=self.cat.pers(nom), fonction=fonction))
    def norme(self, doc, nid, role, par=None, page=None):
        self.t['document_norme'].append(dict(document_id=doc, norme_id=nid, role=role, paragraphe=par, source_page_id=page))
    def essai(self, doc, eid, role='justification', page=None):
        self.t['document_essai'].append(dict(document_id=doc, essai_id=eid, role=role, source_page_id=page))
    def sysdoc(self, doc, sid, role='principal', page=None):
        self.t['document_systeme'].append(dict(document_id=doc, systeme_id=sid, role=role, source_page_id=page))
    def config(self, doc, code, lib, typo, sysid, vmin=None, vmax=None, ineg=None, vitree=1, parent=None, page=None):
        cid = f'CFG-{doc[4:]}-{code}'
        self.t['configuration'].append(dict(id=cid, document_id=doc, code=code, libelle=lib, typologie_code=typo,
            systeme_id=sysid, nb_vantaux_min=vmin, nb_vantaux_max=vmax, vantaux_inegaux=ineg, vitree=vitree,
            parent_configuration_id=parent, source_page_id=page))
        return cid
    def perf_feu(self, doc, cfg, ecrit, classe, duree, e=1, i=0, vi=None, w=0, c=0, s=0, sens=None, cond=None,
                 page=None, statut='extrait'):
        pid = self._id(f'PRF-{doc[4:]}')
        self.t['performance'].append(dict(id=pid, document_id=doc, configuration_id=cfg, domaine_code='feu',
            libelle_tel_qu_ecrit=ecrit, classe_normalisee=classe, nature_code='classement', condition_texte=cond,
            source_page_id=page, statut_extraction=statut))
        self.t['perf_feu'].append(dict(performance_id=pid, critere_r=0, critere_e=e, critere_i=i, variante_i=vi,
            critere_w=w, critere_m=0, critere_c=c, classe_c=None, critere_s=s, duree_min=duree, sens_feu=sens))
        return pid
    def comp(self, doc, ref, fab, cat, role, desig, cfg=None, loc=None, statut='autorise', cond=None, page=None,
             parent=None, role_parent=None, typed=None, carac=(), brute=None, qmin=None, xstat='extrait',
             refcat=None):
        rid = self.cat.ref(ref, fab, refcat or cat, desig) if ref else None
        if ref and brute and brute != ref:
            self.cat.ref_alias(rid, brute, 'ecriture_document', doc)
        dcid = self._id(f'DC-{doc[4:]}')
        self.t['document_composant'].append(dict(id=dcid, document_id=doc, configuration_id=cfg, reference_id=rid,
            reference_brute=(brute or ref), designation_document=desig, categorie_code=cat, role_code=role,
            localisation_code=loc, statut_autorisation_code=statut, quantite_min=qmin, condition_texte=cond,
            parent_id=parent, role_dans_parent=role_parent, source_page_id=page, statut_extraction=xstat))
        if typed:
            tname, vals = typed
            self.t[tname].append(dict(document_composant_id=dcid, **vals))
        for c in carac:
            typ, orig = c[0], c[1]
            num = c[2] if len(c) > 2 else None
            txt = c[3] if len(c) > 3 else None
            unite = c[4] if len(c) > 4 else None
            b = c[5] if len(c) > 5 else None
            self.t['caracteristique_document'].append(dict(id=self._id(f'CAR-{doc[4:]}'), document_composant_id=dcid,
                type_caracteristique_code=typ, valeur_origine=orig, valeur_texte=txt, valeur_num=num, valeur_bool=b,
                unite_origine=unite, nature_code='nominal', source_page_id=page))
        return dcid
    def fmt(self, doc, objet, lib, dims, cfg=None, dc=None, groupe=None, orient=None, page=None, statut='extrait'):
        fid = self._id(f'FMT-{doc[4:]}')
        self.t['dimension_format'].append(dict(id=fid, document_id=doc, configuration_id=cfg, document_composant_id=dc,
            objet_code=objet, libelle=lib, groupe_alternative=groupe, orientation=orient, source_page_id=page,
            statut_extraction=statut))
        for d in dims:
            g, nat, op, orig = d[0], d[1], d[2], d[3]
            unite = d[4] if len(d) > 4 else 'mm'
            val = d[5] if len(d) > 5 else None
            sl = 1 if orig == 'sans limite' or orig == 'illimitée' else 0
            if val is None and not sl:
                try: val = float(str(orig).replace(',', '.'))
                except ValueError: val = None
            un = {'mm':'mm','m²':'m2','m2':'m2','°':'deg','µm':'um'}.get(unite, unite)
            dst = d[6] if len(d) > 6 else statut
            self.t['dimension'].append(dict(id=f'{fid}-{g}-{nat}', format_id=fid, grandeur_code=g, nature_code=nat,
                operateur_code=op, valeur_origine=str(orig), unite_origine=None if sl else unite,
                valeur_norm=None if sl else val, unite_norm_code=un, sans_limite=sl, tolerance_plus=None,
                tolerance_moins=None, statut_extraction=dst))
        return fid
    def support(self, doc, typ, cfg=None, mv=None, mvop=None, ep=None, epop=None, pv=None, prolong=None, imposte=None,
                allege=None, pas=None, cond=None, page=None):
        sid = self._id(f'SUP-{doc[4:]}')
        self.t['support_pose'].append(dict(id=sid, document_id=doc, configuration_id=cfg, type_support_code=typ,
            masse_vol_min_kg_m3=mv, masse_vol_operateur_code=mvop, epaisseur_min_mm=ep, epaisseur_operateur_code=epop,
            classement_pv_exige=pv, prolongation_laterale=prolong, imposte_autorisee=imposte, allege_autorisee=allege,
            pas_fixation_max_mm=pas, condition_texte=cond, source_page_id=page))
        return sid
    def restr(self, doc, typ, lib, texte=None, cfg=None, dc=None, page=None):
        rid = self._id(f'RST-{doc[4:]}')
        self.t['restriction'].append(dict(id=rid, document_id=doc, configuration_id=cfg, document_composant_id=dc,
            type_code=typ, libelle=lib, texte_source=texte, source_page_id=page))
        return rid
    def ctrl(self, doc, typ, desc, table=None, ligne=None, page=None):
        cid = self._id(f'CTL-{(doc or self.fid)[4:]}')
        self.t['controle_humain'].append(dict(id=cid, document_id=doc, table_cible=table, ligne_id=ligne, type_code=typ,
            description=desc, statut='ouvert', resolution=None, source_page_id=page))
        return cid
    def dump(self, path):
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.t, f, ensure_ascii=False, indent=1)
