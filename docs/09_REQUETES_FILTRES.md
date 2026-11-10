# 11. Requêtes SQL de filtre (sql.js)

Source exécutable : [`queries/filtres.sql`](../queries/filtres.sql). Toutes testées par `scripts/test_queries.py` ; extraits réels ci-dessous (3 premières lignes). En JS : `db.prepare(sql).bind({":ref": "907724"})`.

## Q01_recherche_reference

Toutes les occurrences d'une référence (exacte ou partielle, normalisée ou alias) avec PV de rattachement et validité effective

- **Paramètres (interface)** : `{":ref": "907724"}`
- **Tables / vues** : `configuration`, `document`, `document_composant`, `organisme`, `q`, `reference_alias`, `reference_composant`, `source_page`, `v_document_rattachement`, `v_validite_effective`
- **Résultat sur le corpus** : 2 ligne(s)

```sql
WITH q AS (SELECT upper(replace(replace(:ref,' ',''),'.','')) AS r)
SELECT d.numero_normalise AS document, d.type_code, pv.numero_normalise AS pv_principal,
       ve.date_validite_effective, dc.reference_brute, rc.reference_normalisee, o.nom AS fabricant,
       dc.categorie_code, dc.role_code, dc.localisation_code, dc.statut_autorisation_code,
       dc.designation_document, c.libelle AS configuration, sp.page_doc, sp.section, sp.planche, dc.statut_extraction
FROM document_composant dc
JOIN q
LEFT JOIN reference_composant rc ON rc.id = dc.reference_id
LEFT JOIN organisme o ON o.id = rc.fabricant_id
JOIN document d ON d.id = dc.document_id
JOIN v_document_rattachement ra ON ra.document_id = d.id
JOIN document pv ON pv.id = ra.pv_principal_id
LEFT JOIN v_validite_effective ve ON ve.document_id = pv.id
LEFT JOIN configuration c ON c.id = dc.configuration_id
LEFT JOIN source_page sp ON sp.id = dc.source_page_id
WHERE rc.reference_normalisee LIKE '%' || q.r || '%'
   OR dc.reference_id IN (SELECT reference_id FROM reference_alias WHERE upper(replace(replace(alias,' ',''),'.','')) LIKE '%' || q.r || '%')
ORDER BY pv.numero_normalise, d.numero_normalise;
```

Exemple de résultat :

```json
[
 {
  "document": "11-A-507",
  "type_code": "pv_classement",
  "pv_principal": "11-A-507",
  "date_validite_effective": "2027-04-12",
  "reference_brute": "907724",
  "reference_normalisee": "907724",
  "fabricant": "FORSTER PROFILSYSTEME AG",
  "categorie_code": "kit_serrure",
  "role_code": "condamnation",
  "localisation_code": "vantail",
  "statut_autorisation_code": "autorise",
  "designation_document": "Serrure 1 point classique (béquille et/ou push-bar) — fonction E avec AP, DIN G",
  "configuration": "Bloc-porte 1 vantail",
  "page_doc": 42,
  "section": null,
  "planche": "Planche 30",
  "statut_extraction": "extrait"
 },
 {
  "document": "11-A-507",
  "type_code": "pv_classement",
  "pv_principal": "11-A-507",
  "date_validite_effective": "2027-04-12",
  "reference_brute": "907724",
  "reference_normalisee": "907724",
  "fabricant": "FORSTER PROFILSYSTEME AG",
  "categorie_code": "kit_serrure",
  "role_code": "condamnation",
  "localisation_code": "vantail_principal",
  "statut_autorisation_code": "autorise",
  "designation_document": "Serrure 1 point classique (béquille et/ou push-bar) — fonction E avec AP, DIN G",
  "configuration": "Bloc-porte 2 vantaux égaux ou inégaux",
  "page_doc": 45,
  "section": null,
  "planche": "Planche 33",
  "statut_extraction": "extrait"
 }
]
```

## Q02_serrures_par_fonction

Serrures / kits par fonction, nombre de points, antipanique, main DIN et vantail (NULL = pas de filtre)

- **Paramètres (interface)** : `{":fonction": "E", ":nb_points": 2, ":antipanique": 1, ":main": null, ":vantail": null}`
- **Tables / vues** : `configuration`, `dc_serrure`, `document`, `document_composant`, `source_page`
- **Résultat sur le corpus** : 6 ligne(s)

```sql
SELECT d.numero_normalise AS document, dc.reference_brute, s.type_serrure_code, s.fonction_code, s.nb_points,
       s.point_haut, s.point_median, s.point_bas, s.antipanique, s.main_din, s.version, s.vantail,
       (SELECT group_concat(e.role_dans_parent || '=' || e.reference_brute, ' ; ') FROM document_composant e WHERE e.parent_id = dc.id) AS composition,
       c.libelle AS configuration, sp.planche, sp.page_doc, dc.statut_extraction
FROM dc_serrure s
JOIN document_composant dc ON dc.id = s.document_composant_id
JOIN document d ON d.id = dc.document_id
LEFT JOIN configuration c ON c.id = dc.configuration_id
LEFT JOIN source_page sp ON sp.id = dc.source_page_id
WHERE (:fonction IS NULL OR s.fonction_code = :fonction)
  AND (:nb_points IS NULL OR s.nb_points = :nb_points)
  AND (:antipanique IS NULL OR s.antipanique = :antipanique)
  AND (:main IS NULL OR s.main_din = :main)
  AND (:vantail IS NULL OR s.vantail = :vantail)
ORDER BY d.numero_normalise, s.main_din, dc.reference_brute;
```

Exemple de résultat :

```json
[
 {
  "document": "11-A-507",
  "reference_brute": "917737",
  "type_serrure_code": "mortaiser",
  "fonction_code": "E",
  "nb_points": 2,
  "point_haut": 1,
  "point_median": 1,
  "point_bas": 0,
  "antipanique": 1,
  "main_din": "D",
  "version": "classique",
  "vantail": "unique",
  "composition": "coffre=907237 ; gache=907001",
  "configuration": "Bloc-porte 1 vantail",
  "planche": "Planche 30",
  "page_doc": 42,
  "statut_extraction": "extrait"
 },
 {
  "document": "11-A-507",
  "reference_brute": "917737",
  "type_serrure_code": "mortaiser",
  "fonction_code": "E",
  "nb_points": 2,
  "point_haut": 1,
  "point_median": 1,
  "point_bas": 0,
  "antipanique": 1,
  "main_din": "D",
  "version": "classique",
  "vantail": "principal",
  "composition": "coffre=907237 ; gache=907001",
  "configuration": "Bloc-porte 2 vantaux égaux ou inégaux",
  "planche": "Planche 33",
  "page_doc": 45,
  "statut_extraction": "extrait"
 }
]
```

## Q03_documents_par_systeme

Documents (PV + extensions) concernant un système Forster, avec classements et validité effective

- **Paramètres (interface)** : `{":systeme": "FUEGO LIGHT 30"}`
- **Tables / vues** : `document`, `document_systeme`, `performance`, `systeme`, `v_validite_effective`
- **Résultat sur le corpus** : 3 ligne(s)

```sql
SELECT s.nom AS systeme, ds.role, d.numero_normalise, d.type_code, d.objet,
       (SELECT group_concat(DISTINCT p.classe_normalisee) FROM performance p WHERE p.document_id = d.id) AS classements,
       ve.date_validite_effective, ve.derniere_reconduction
FROM document_systeme ds
JOIN systeme s ON s.id = ds.systeme_id
JOIN document d ON d.id = ds.document_id
LEFT JOIN v_validite_effective ve ON ve.document_id = d.id
WHERE s.nom_normalise = upper(:systeme)
ORDER BY d.date_emission;
```

Exemple de résultat :

```json
[
 {
  "systeme": "Fuego Light 30",
  "role": "integration",
  "numero_normalise": "11-A-507",
  "type_code": "pv_classement",
  "objet": "Bloc-porte à un ou deux vantaux, égaux ou inégaux, à ossature métallique — profils acier Presto 50 ; vitrages PYROSWISS, PYROSWISS STADIP, PYROSWISS CLIMAPLUS",
  "classements": "E 30",
  "date_validite_effective": "2027-04-12",
  "derniere_reconduction": "11-A-507/REC-22/2"
 },
 {
  "systeme": "Fuego Light 30",
  "role": "principal",
  "numero_normalise": "EFR-21-002687",
  "type_code": "pv_classement",
  "objet": "Cloison à ossature thermiquement isolée avec vitrages collés bord à bord à joints verticaux — Fuego Light 30 ; vitrages CONTRAFLAM STRUCTURE 30",
  "classements": "EI 30,EW 30,E 30",
  "date_validite_effective": "2027-07-07",
  "derniere_reconduction": null
 }
]
```

## Q04_par_performance

Configurations classées au moins à une durée donnée pour une combinaison de critères (ex. EI ≥ 60)

- **Paramètres (interface)** : `{":duree_min": 60, ":exige_i": 1, ":exige_w": 0, ":typologie": null}`
- **Tables / vues** : `v_classement_feu`, `v_document_rattachement`, `v_validite_effective`
- **Résultat sur le corpus** : 2 ligne(s)

```sql
SELECT v.numero_normalise AS document, v.configuration, v.typologie_code, v.systeme, v.classe_normalisee,
       v.duree_min, v.condition_texte, v.page_doc, v.section, ve.date_validite_effective
FROM v_classement_feu v
JOIN v_document_rattachement ra ON ra.document_id = v.document_id
LEFT JOIN v_validite_effective ve ON ve.document_id = ra.pv_principal_id
WHERE v.duree_min >= :duree_min
  AND (:exige_i = 0 OR v.critere_i = 1)
  AND (:exige_w = 0 OR v.critere_w = 1)
  AND (:typologie IS NULL OR v.typologie_code = :typologie)
ORDER BY v.duree_min DESC, v.numero_normalise;
```

Exemple de résultat :

```json
[
 {
  "document": "08-A-275",
  "configuration": "Cloison vitrée Fuego Light 60",
  "typologie_code": "cloison_vitree",
  "systeme": "Fuego Light 60",
  "classe_normalisee": "EI 60",
  "duree_min": 60,
  "condition_texte": null,
  "page_doc": 7,
  "section": "§3.2",
  "date_validite_effective": "2029-02-16"
 },
 {
  "document": "13-A-704",
  "configuration": "Façade vitrée Thermfix Vario (séries 45 et 60)",
  "typologie_code": "facade_vitree",
  "systeme": "Thermfix Vario",
  "classe_normalisee": "EI 60",
  "duree_min": 60,
  "condition_texte": null,
  "page_doc": 6,
  "section": "§4.2",
  "date_validite_effective": "2028-12-03"
 }
]
```

## Q05_passage_libre_minimal

Blocs-portes dont le passage libre / vantail autorisé atteint au moins L x H demandés (valeurs AUTORISÉES uniquement)

- **Paramètres (interface)** : `{":largeur": 1400, ":hauteur": 2500}`
- **Tables / vues** : `configuration`, `dimension`, `dimension_format`, `document`, `source_page`
- **Résultat sur le corpus** : 5 ligne(s)

```sql
SELECT df.document_id, d.numero_normalise, df.objet_code, df.libelle, c.libelle AS configuration,
       MAX(CASE WHEN dm.grandeur_code='largeur' AND dm.nature_code='autorise_max' THEN coalesce(dm.valeur_norm, 1e9) END) AS largeur_max,
       MAX(CASE WHEN dm.grandeur_code='hauteur' AND dm.nature_code='autorise_max' THEN coalesce(dm.valeur_norm, 1e9) END) AS hauteur_max,
       MAX(CASE WHEN dm.grandeur_code='surface' AND dm.nature_code='autorise_max' THEN dm.valeur_norm END) AS surface_max_m2,
       sp.page_doc, sp.section
FROM dimension_format df
JOIN dimension dm ON dm.format_id = df.id
JOIN document d ON d.id = df.document_id
LEFT JOIN configuration c ON c.id = df.configuration_id
LEFT JOIN source_page sp ON sp.id = df.source_page_id
WHERE df.objet_code IN ('passage_libre','vantail_hors_tout')
GROUP BY df.id
HAVING largeur_max >= :largeur AND hauteur_max >= :hauteur
   AND (surface_max_m2 IS NULL OR surface_max_m2 >= (:largeur * :hauteur) / 1e6)
ORDER BY d.numero_normalise;
```

Exemple de résultat :

```json
[
 {
  "document_id": "DOC-11-A-507",
  "numero_normalise": "11-A-507",
  "objet_code": "passage_libre",
  "libelle": "Passage libre — 1 vantail",
  "configuration": "Bloc-porte 1 vantail",
  "largeur_max": 1610.0,
  "hauteur_max": 3105.0,
  "surface_max_m2": 4.54,
  "page_doc": 11,
  "section": "§4.3.2"
 },
 {
  "document_id": "DOC-11-A-507",
  "numero_normalise": "11-A-507",
  "objet_code": "passage_libre",
  "libelle": "Passage libre — 2 vantaux égaux et inégaux",
  "configuration": "Bloc-porte 2 vantaux égaux ou inégaux",
  "largeur_max": 2767.0,
  "hauteur_max": 3272.0,
  "surface_max_m2": 8.4,
  "page_doc": 11,
  "section": "§4.3.2"
 }
]
```

## Q06_vitrage_dimension

Vitrages dont UN format autorisé couvre L x H (gère portrait/paysage et surface max)

- **Paramètres (interface)** : `{":largeur": 1500, ":hauteur": 2500, ":gamme": null}`
- **Tables / vues** : `dc_vitrage`, `dimension`, `dimension_format`, `document`, `source_page`
- **Résultat sur le corpus** : 27 ligne(s)

```sql
SELECT d.numero_normalise AS document, v.gamme, v.designation, v.type_vitrage_code, df.libelle AS format,
       MAX(CASE WHEN dm.grandeur_code='largeur' AND dm.nature_code='autorise_max' THEN dm.valeur_norm END) AS l_max,
       MAX(CASE WHEN dm.grandeur_code='hauteur' AND dm.nature_code='autorise_max' THEN dm.valeur_norm END) AS h_max,
       MAX(CASE WHEN dm.grandeur_code='surface' AND dm.nature_code='autorise_max' THEN dm.valeur_norm END) AS s_max,
       df.objet_code, df.statut_extraction, sp.page_doc, sp.section
FROM dimension_format df
JOIN dc_vitrage v ON v.document_composant_id = df.document_composant_id
JOIN dimension dm ON dm.format_id = df.id
JOIN document d ON d.id = df.document_id
LEFT JOIN source_page sp ON sp.id = df.source_page_id
WHERE df.objet_code IN ('vitrage_hors_tout','vitrage_clair')
  AND (:gamme IS NULL OR v.gamme LIKE '%' || :gamme || '%')
GROUP BY df.id
HAVING l_max >= :largeur AND h_max >= :hauteur AND (s_max IS NULL OR s_max >= (:largeur * :hauteur) / 1e6)
ORDER BY d.numero_normalise, v.designation;
```

Exemple de résultat :

```json
[
 {
  "document": "08-A-275",
  "gamme": "PYROSTOP",
  "designation": "Pyrostop 60-101",
  "type_vitrage_code": "monolithique",
  "format": "Pyrostop 60-101 — portrait",
  "l_max": 1500.0,
  "h_max": 2530.0,
  "s_max": null,
  "objet_code": "vitrage_clair",
  "statut_extraction": "extrait",
  "page_doc": 8,
  "section": "§4.3.2"
 },
 {
  "document": "08-A-275/EXT-20/2",
  "gamme": "PYROSTOP",
  "designation": "Pyrostop 60-101 ou 60-201 monté en isolant",
  "type_vitrage_code": "isolant",
  "format": "Pyrostop 60-101/60-201 isolant sans store 1540 x 2500",
  "l_max": 1540.0,
  "h_max": 2500.0,
  "s_max": null,
  "objet_code": "vitrage_hors_tout",
  "statut_extraction": "extrait",
  "page_doc": 3,
  "section": "§3-§4"
 }
]
```

## Q07_contenu_fichier_source

Inventaire d'un fichier PDF source : documents logiques, ordre, pages, statut

- **Paramètres (interface)** : `{":fichier": "FIC-11-A-507"}`
- **Tables / vues** : `dimension_format`, `document`, `document_composant`, `fichier_source`
- **Résultat sur le corpus** : 6 ligne(s)

```sql
SELECT f.nom_fichier, d.ordre_dans_fichier, d.numero, d.type_code, d.date_emission, d.date_validite, d.nb_pages, d.statut_extraction,
       (SELECT count(*) FROM document_composant dc WHERE dc.document_id = d.id) AS nb_composants,
       (SELECT count(*) FROM dimension_format x WHERE x.document_id = d.id) AS nb_formats_dim
FROM document d JOIN fichier_source f ON f.id = d.fichier_source_id
WHERE f.id = :fichier
ORDER BY d.ordre_dans_fichier;
```

Exemple de résultat :

```json
[
 {
  "nom_fichier": "FR 11-A-507 - VETR - porte PRESTO E30 - COPRO - 12-04-2027.pdf",
  "ordre_dans_fichier": 1,
  "numero": "22/2 - Révision 1",
  "type_code": "reconduction",
  "date_emission": "2022-09-13",
  "date_validite": "2027-04-12",
  "nb_pages": 2,
  "statut_extraction": "extrait",
  "nb_composants": 0,
  "nb_formats_dim": 0
 },
 {
  "nom_fichier": "FR 11-A-507 - VETR - porte PRESTO E30 - COPRO - 12-04-2027.pdf",
  "ordre_dans_fichier": 2,
  "numero": "17/1",
  "type_code": "reconduction",
  "date_emission": "2017-06-06",
  "date_validite": "2022-04-12",
  "nb_pages": 1,
  "statut_extraction": "extrait",
  "nb_composants": 0,
  "nb_formats_dim": 0
 }
]
```

## Q08_documents_lies_a_un_pv

Extensions, reconductions, remplacements et règles de cumul autour d'un PV principal

- **Paramètres (interface)** : `{":pv": "11-A-507"}`
- **Tables / vues** : `document`, `document_relation`
- **Résultat sur le corpus** : 17 ligne(s)

```sql
SELECT pv.numero_normalise AS pv, dr.type_relation_code, src.numero_normalise AS document_source, src.type_code AS type_source,
       cib.numero_normalise AS document_cible, src.date_emission, src.date_validite, src.present_dans_corpus,
       dr.commentaire
FROM document pv
JOIN document_relation dr ON dr.document_cible_id = pv.id OR dr.document_source_id = pv.id
   OR dr.document_source_id IN (SELECT r.document_source_id FROM document_relation r WHERE r.document_cible_id = pv.id AND r.type_relation_code IN ('etend','reconduit'))
JOIN document src ON src.id = dr.document_source_id
JOIN document cib ON cib.id = dr.document_cible_id
WHERE pv.numero_normalise = :pv AND pv.type_code = 'pv_classement'
ORDER BY src.date_emission, dr.type_relation_code;
```

Exemple de résultat :

```json
[
 {
  "pv": "11-A-507",
  "type_relation_code": "a_pour_reference",
  "document_source": "11-A-507",
  "type_source": "pv_classement",
  "document_cible": "11-A-507/RAPPORT",
  "date_emission": "2012-04-12",
  "date_validite": "2017-04-12",
  "present_dans_corpus": 1,
  "commentaire": null
 },
 {
  "pv": "11-A-507",
  "type_relation_code": "support_associe",
  "document_source": "11-A-507",
  "type_source": "pv_classement",
  "document_cible": "10-A-650",
  "date_emission": "2012-04-12",
  "date_validite": "2017-04-12",
  "present_dans_corpus": 1,
  "commentaire": "Cloison vitrée E30 ou E60"
 }
]
```

## Q09_restrictions_applicables

Restrictions d'un PV et de ses extensions, filtrables par type

- **Paramètres (interface)** : `{":pv": "EFR-24-000553", ":type": null}`
- **Tables / vues** : `configuration`, `document`, `document_composant`, `restriction`, `source_page`, `v_document_rattachement`
- **Résultat sur le corpus** : 12 ligne(s)

```sql
SELECT d.numero_normalise AS document, r.type_code, r.libelle, r.texte_source, c.libelle AS configuration,
       dc.reference_brute AS composant, sp.page_doc, sp.section
FROM restriction r
JOIN document d ON d.id = r.document_id
JOIN v_document_rattachement ra ON ra.document_id = d.id
JOIN document pv ON pv.id = ra.pv_principal_id
LEFT JOIN configuration c ON c.id = r.configuration_id
LEFT JOIN document_composant dc ON dc.id = r.document_composant_id
LEFT JOIN source_page sp ON sp.id = r.source_page_id
WHERE pv.numero_normalise = :pv AND (:type IS NULL OR r.type_code = :type)
ORDER BY r.type_code, d.numero_normalise;
```

Exemple de résultat :

```json
[
 {
  "document": "EFR-24-000553",
  "type_code": "condition_combinaison",
  "libelle": "Semi-fixe sans verrouillage uniquement si principal équipé d'une serrure 2 points (haut et médian)",
  "texte_source": null,
  "configuration": "Bloc-porte 2 vantaux égaux ou inégaux",
  "composant": null,
  "page_doc": 6,
  "section": "§3.3.5.2"
 },
 {
  "document": "EFR-24-000553",
  "type_code": "condition_mise_en_oeuvre",
  "libelle": "TV 100 : traverse haute, côté feu uniquement",
  "texte_source": null,
  "configuration": null,
  "composant": "TV 100",
  "page_doc": 6,
  "section": "§3.3.5.2"
 }
]
```

## Q10_paumelles

Articulations par type, mode de fixation et réglage

- **Paramètres (interface)** : `{":mode": "visser", ":reglage": "3D"}`
- **Tables / vues** : `dc_articulation`, `document`, `document_composant`, `source_page`
- **Résultat sur le corpus** : 4 ligne(s)

```sql
SELECT d.numero_normalise AS document, dc.reference_brute, a.type_articulation_code, a.mode_fixation, a.reglage,
       a.distance_extremite_mm, dc.condition_texte, sp.page_doc, sp.section
FROM dc_articulation a
JOIN document_composant dc ON dc.id = a.document_composant_id
JOIN document d ON d.id = dc.document_id
LEFT JOIN source_page sp ON sp.id = dc.source_page_id
WHERE (:mode IS NULL OR a.mode_fixation = :mode) AND (:reglage IS NULL OR a.reglage = :reglage)
ORDER BY d.numero_normalise, dc.reference_brute;
```

Exemple de résultat :

```json
[
 {
  "document": "EFR-24-000553",
  "reference_brute": "907670",
  "type_articulation_code": "paumelle",
  "mode_fixation": "visser",
  "reglage": "3D",
  "distance_extremite_mm": 140.0,
  "condition_texte": "pl. 28 ; à 140 mm des extrémités",
  "page_doc": 6,
  "section": "§3.3.5.1"
 },
 {
  "document": "EFR-24-000553",
  "reference_brute": "907671",
  "type_articulation_code": "paumelle",
  "mode_fixation": "visser",
  "reglage": "3D",
  "distance_extremite_mm": 140.0,
  "condition_texte": "pl. 28 ; à 140 mm des extrémités",
  "page_doc": 6,
  "section": "§3.3.5.1"
 }
]
```

## Q11_ferme_portes_cote_oppose

Ferme-portes autorisés côté opposé au feu (et protection exigée) — NULL = non précisé par le document

- **Paramètres (interface)** : `{}`
- **Tables / vues** : `dc_ferme_porte`, `document`, `document_composant`, `organisme`, `reference_composant`, `source_page`
- **Résultat sur le corpus** : 17 ligne(s)

```sql
SELECT d.numero_normalise AS document, dc.reference_brute, o.nom AS fabricant, f.type_ferme_porte_code,
       f.cote_feu_autorise, f.cote_oppose_autorise, f.protection_requise, sp.page_doc, dc.statut_extraction
FROM dc_ferme_porte f
JOIN document_composant dc ON dc.id = f.document_composant_id
JOIN document d ON d.id = dc.document_id
LEFT JOIN reference_composant rc ON rc.id = dc.reference_id
LEFT JOIN organisme o ON o.id = rc.fabricant_id
LEFT JOIN source_page sp ON sp.id = dc.source_page_id
WHERE f.cote_oppose_autorise = 1
ORDER BY d.numero_normalise, dc.reference_brute;
```

Exemple de résultat :

```json
[
 {
  "document": "11-A-507",
  "reference_brute": "1593",
  "fabricant": "DORMA (dormakaba)",
  "type_ferme_porte_code": "applique",
  "cote_feu_autorise": 0,
  "cote_oppose_autorise": 1,
  "protection_requise": "Kit de protection 904001 (FORSTER)",
  "page_doc": 7,
  "statut_extraction": "a_verifier"
 },
 {
  "document": "11-A-507",
  "reference_brute": "HL100",
  "fabricant": "LEVASSEUR",
  "type_ferme_porte_code": "applique",
  "cote_feu_autorise": 1,
  "cote_oppose_autorise": 1,
  "protection_requise": "Plaque PROMATECT H ou SUPALUX 10 mm (côté opposé au feu)",
  "page_doc": 7,
  "statut_extraction": "extrait"
 }
]
```

## Q12_pv_valides_a_date

PV principaux valides à une date (dernière reconduction présente dans le corpus)

- **Paramètres (interface)** : `{":date": "2026-11-10"}`
- **Tables / vues** : `document`, `v_validite_effective`
- **Résultat sur le corpus** : 6 ligne(s)

```sql
SELECT ve.numero_normalise, ve.date_validite_initiale, ve.date_validite_effective, ve.derniere_reconduction, d.objet
FROM v_validite_effective ve JOIN document d ON d.id = ve.document_id
WHERE d.present_dans_corpus = 1 AND ve.date_validite_effective >= :date
ORDER BY ve.date_validite_effective;
```

Exemple de résultat :

```json
[
 {
  "numero_normalise": "11-A-507",
  "date_validite_initiale": "2017-04-12",
  "date_validite_effective": "2027-04-12",
  "derniere_reconduction": "11-A-507/REC-22/2",
  "objet": "Bloc-porte à un ou deux vantaux, égaux ou inégaux, à ossature métallique — profils acier Presto 50 ; vitrages PYROSWISS, PYROSWISS STADIP, PYROSWISS CLIMAPLUS"
 },
 {
  "numero_normalise": "EFR-21-002687",
  "date_validite_initiale": "2027-07-07",
  "date_validite_effective": "2027-07-07",
  "derniere_reconduction": null,
  "objet": "Cloison à ossature thermiquement isolée avec vitrages collés bord à bord à joints verticaux — Fuego Light 30 ; vitrages CONTRAFLAM STRUCTURE 30"
 }
]
```

## Q13_recherche_texte

Recherche libre insensible à la casse/aux accents (mots normalisés côté appli)

- **Paramètres (interface)** : `{":texte": "antipanique"}`
- **Tables / vues** : `document`, `recherche_index`
- **Résultat sur le corpus** : 21 ligne(s)

```sql
SELECT ri.objet_type, ri.objet_id, d.numero_normalise, substr(ri.texte, 1, 160) AS extrait
FROM recherche_index ri LEFT JOIN document d ON d.id = ri.document_id
WHERE ri.texte LIKE '%' || lower(:texte) || '%'
ORDER BY d.numero_normalise LIMIT 200;
```

Exemple de résultat :

```json
[
 {
  "objet_type": "document_composant",
  "objet_id": "DC-11-A-507-0103",
  "numero_normalise": "11-A-507",
  "extrait": "  cremone encastree a levier avec tetiere 1 point (haut), sans antipanique serrure  (pl. 34, 36)"
 },
 {
  "objet_type": "document_composant",
  "objet_id": "DC-11-A-507-0104",
  "numero_normalise": "11-A-507",
  "extrait": "  cremone encastree a levier avec tetiere 2 points (haut et bas), sans antipanique serrure  (pl. 34, 37)"
 }
]
```

## Q14_fiche_reference

Fiche d'une référence : données document et données d'enrichissement, jamais fusionnées

- **Paramètres (interface)** : `{":ref": "HZ43F"}`
- **Tables / vues** : `document`, `document_composant`, `reference_composant`, `v_reference_fiche`
- **Résultat sur le corpus** : 5 ligne(s)

```sql
SELECT * FROM v_reference_fiche WHERE reference_normalisee = upper(replace(replace(:ref,' ',''),'.',''))
UNION ALL
SELECT rc.id, rc.reference_normalisee, 'document', 'occurrence', dc.designation_document || ' [' || dc.statut_autorisation_code || ']', NULL, d.numero_normalise
FROM reference_composant rc JOIN document_composant dc ON dc.reference_id = rc.id JOIN document d ON d.id = dc.document_id
WHERE rc.reference_normalisee = upper(replace(replace(:ref,' ',''),'.',''));
```

Exemple de résultat :

```json
[
 {
  "reference_id": "REF-DORMA-HZ43F",
  "reference_normalisee": "HZ43F",
  "source": "enrichissement",
  "caracteristique": "fonction",
  "valeur": "Verrouillage automatique du battant semi-fixe (portes 2 vantaux)",
  "statut_fiabilite": "confirme",
  "origine": "dormakaba — brochure technique HZ 43-F (FR)"
 },
 {
  "reference_id": "REF-DORMA-HZ43F",
  "reference_normalisee": "HZ43F",
  "source": "enrichissement",
  "caracteristique": "gamme",
  "valeur": "Variantes HZ 43-F22 et HZ 43-F24 (DIN-L / DIN-R)",
  "statut_fiabilite": "confirme",
  "origine": "dormakaba — Technikprospekt HZ 43-F (DE)"
 }
]
```

## Q15_controles_ouverts

Points de contrôle humain ouverts par document

- **Paramètres (interface)** : `{":type": null}`
- **Tables / vues** : `controle_humain`, `document`, `source_page`
- **Résultat sur le corpus** : 32 ligne(s)

```sql
SELECT d.numero_normalise, ch.type_code, ch.description, sp.page_doc, sp.section, sp.planche
FROM controle_humain ch LEFT JOIN document d ON d.id = ch.document_id LEFT JOIN source_page sp ON sp.id = ch.source_page_id
WHERE ch.statut = 'ouvert' AND (:type IS NULL OR ch.type_code = :type)
ORDER BY d.numero_normalise;
```

Exemple de résultat :

```json
[
 {
  "numero_normalise": "08-A-275",
  "type_code": "ocr_degrade",
  "description": "§4.3.2 : valeur orpheline « 2876 » (hauteur) dans le bloc Pyrostop 60-201 / Isolant — non rattachée ; à vérifier sur l'original.",
  "page_doc": 8,
  "section": "§4.3.2",
  "planche": null
 },
 {
  "numero_normalise": "08-A-275",
  "type_code": "planche_image",
  "description": "Planche 1 (profilés) : seules les références « 736.050 » et « 852 » sont lisibles en OCR — liste complète des profilés à relever visuellement.",
  "page_doc": 11,
  "section": null,
  "planche": "Planche 1"
 }
]
```

## Q16_essais_justificatifs

Essais cités et VALEURS TESTÉES (minutes) — distinctes des classements

- **Paramètres (interface)** : `{":pv": "11-A-507"}`
- **Tables / vues** : `document`, `document_essai`, `essai`, `essai_resultat`, `norme`, `organisme`, `v_document_rattachement`
- **Résultat sur le corpus** : 12 ligne(s)

```sql
SELECT d.numero_normalise AS document, e.reference AS essai, o.nom AS laboratoire, n.code || coalesce(':' || n.annee, '') || coalesce(n.amendement, '') AS norme,
       er.critere_code, er.operateur_code, er.duree_min, er.condition_essai
FROM document_essai de
JOIN document d ON d.id = de.document_id
JOIN v_document_rattachement ra ON ra.document_id = d.id
JOIN document pv ON pv.id = ra.pv_principal_id
JOIN essai e ON e.id = de.essai_id
LEFT JOIN organisme o ON o.id = e.laboratoire_id
LEFT JOIN norme n ON n.id = e.norme_id
LEFT JOIN essai_resultat er ON er.essai_id = e.id
WHERE pv.numero_normalise = :pv
ORDER BY d.numero_normalise, e.reference, er.critere_code;
```

Exemple de résultat :

```json
[
 {
  "document": "11-A-507/EXT-22/2",
  "essai": "EFR-21-002096-B",
  "laboratoire": "Efectis France",
  "norme": "EN 1634-1+A1:2018",
  "critere_code": "E",
  "operateur_code": "eq",
  "duree_min": 31.0,
  "condition_essai": null
 },
 {
  "document": "11-A-507/EXT-22/2",
  "essai": "EFR-21-002096-B",
  "laboratoire": "Efectis France",
  "norme": "EN 1634-1+A1:2018",
  "critere_code": "W",
  "operateur_code": "eq",
  "duree_min": 14.0,
  "condition_essai": null
 }
]
```

## Q17_joints

Joints par type et section

- **Paramètres (interface)** : `{":type": "fibre_minerale", ":epaisseur": 5}`
- **Tables / vues** : `dc_joint`, `document`, `document_composant`
- **Résultat sur le corpus** : 5 ligne(s)

```sql
SELECT d.numero_normalise, dc.reference_brute, j.type_joint_code, j.largeur_mm, j.epaisseur_mm, j.epaisseur_min_mm, j.epaisseur_max_mm, j.position, j.marque_produit
FROM dc_joint j JOIN document_composant dc ON dc.id = j.document_composant_id JOIN document d ON d.id = dc.document_id
WHERE (:type IS NULL OR j.type_joint_code = :type)
  AND (:epaisseur IS NULL OR j.epaisseur_mm = :epaisseur OR (:epaisseur BETWEEN j.epaisseur_min_mm AND j.epaisseur_max_mm))
ORDER BY d.numero_normalise, dc.reference_brute;
```

Exemple de résultat :

```json
[
 {
  "numero_normalise": "08-A-275",
  "reference_brute": "948005",
  "type_joint_code": "fibre_minerale",
  "largeur_mm": null,
  "epaisseur_mm": 5.0,
  "epaisseur_min_mm": null,
  "epaisseur_max_mm": null,
  "position": null,
  "marque_produit": null
 },
 {
  "numero_normalise": "11-A-507",
  "reference_brute": "948005",
  "type_joint_code": "fibre_minerale",
  "largeur_mm": 15.0,
  "epaisseur_mm": 5.0,
  "epaisseur_min_mm": null,
  "epaisseur_max_mm": null,
  "position": null,
  "marque_produit": null
 }
]
```

## Q18_supports

Documents autorisant un type de construction support (ex. cloison 98/48 avec allège)

- **Paramètres (interface)** : `{":type_support": "cloison_legere_98_48", ":allege": 1}`
- **Tables / vues** : `document`, `source_page`, `support_pose`
- **Résultat sur le corpus** : 2 ligne(s)

```sql
SELECT d.numero_normalise, s.type_support_code, s.masse_vol_min_kg_m3, s.epaisseur_min_mm, s.classement_pv_exige,
       s.prolongation_laterale, s.imposte_autorisee, s.allege_autorisee, s.pas_fixation_max_mm, s.condition_texte, sp.page_doc, sp.section
FROM support_pose s JOIN document d ON d.id = s.document_id LEFT JOIN source_page sp ON sp.id = s.source_page_id
WHERE s.type_support_code = :type_support AND (:allege IS NULL OR s.allege_autorisee = :allege)
ORDER BY d.numero_normalise;
```

Exemple de résultat :

```json
[
 {
  "numero_normalise": "08-A-275",
  "type_support_code": "cloison_legere_98_48",
  "masse_vol_min_kg_m3": null,
  "epaisseur_min_mm": null,
  "classement_pv_exige": "EI 60",
  "prolongation_laterale": 1,
  "imposte_autorisee": 1,
  "allege_autorisee": 1,
  "pas_fixation_max_mm": 410.0,
  "condition_texte": "Rails R48 6/10, montants M48 ; chevêtre M48 renforcés 15/10 ; HUS Ø7,5x80 pas ~410 ; contreplaques 947 026",
  "page_doc": 6,
  "section": "§1.2.5.3"
 },
 {
  "numero_normalise": "EFR-21-002687",
  "type_support_code": "cloison_legere_98_48",
  "masse_vol_min_kg_m3": null,
  "epaisseur_min_mm": null,
  "classement_pv_exige": "EI 60",
  "prolongation_laterale": 1,
  "imposte_autorisee": 1,
  "allege_autorisee": 1,
  "pas_fixation_max_mm": 600.0,
  "condition_texte": "Placostil (PLACOPLATRE), Prégymétal (LAFARGE), KS ou KF (KNAUF) ; prolongation : montant M48 15/10 ou tube 45x45x2, vis autoforeuses 6,3x120 ; imposte/allège : chevêtre tubes 50x50x4, montants intermédiaires pas ≤ 1300, double BA13 ; jeu périphérique ≤ 25 mm",
  "page_doc": 6,
  "section": "§3.3.4.2"
 }
]
```

## Q19_filtre_combine

Filtre combiné : typologie + classe minimale + présence d'un composant (référence) dans le même PV (ou ses extensions)

- **Paramètres (interface)** : `{":typologie": "bloc_porte", ":duree_min": 30, ":ref": "TS93"}`
- **Tables / vues** : `document`, `document_composant`, `reference_composant`, `v_classement_feu`, `v_document_rattachement`, `v_validite_effective`
- **Résultat sur le corpus** : 5 ligne(s)

```sql
SELECT DISTINCT pv.numero_normalise AS pv, v.classe_normalisee, v.configuration, ve.date_validite_effective,
       dc.reference_brute, d2.numero_normalise AS document_composant
FROM v_classement_feu v
JOIN v_document_rattachement ra ON ra.document_id = v.document_id
JOIN document pv ON pv.id = ra.pv_principal_id
LEFT JOIN v_validite_effective ve ON ve.document_id = pv.id
JOIN v_document_rattachement ra2 ON ra2.pv_principal_id = pv.id
JOIN document_composant dc ON dc.document_id = ra2.document_id
JOIN document d2 ON d2.id = dc.document_id
JOIN reference_composant rc ON rc.id = dc.reference_id
WHERE v.typologie_code = :typologie AND v.duree_min >= :duree_min
  AND rc.reference_normalisee = upper(replace(replace(:ref,' ',''),'.',''))
ORDER BY pv.numero_normalise;
```

Exemple de résultat :

```json
[
 {
  "pv": "11-A-507",
  "classe_normalisee": "E 30",
  "configuration": "Bloc-porte 1 ou 2 vantaux Presto 50",
  "date_validite_effective": "2027-04-12",
  "reference_brute": "TS93",
  "document_composant": "11-A-507"
 },
 {
  "pv": "11-A-507",
  "classe_normalisee": "E 30",
  "configuration": "Bloc-porte 11-A-507 muni de vitrages CONTRAFLAM LITE 30 (mono ou CLIMAPLUS/CLIMALIT)",
  "date_validite_effective": "2027-04-12",
  "reference_brute": "TS93",
  "document_composant": "11-A-507"
 }
]
```

## Q20_valeurs_testees_vs_autorisees

Contrôle : aucune dimension ne mélange natures ; répartition des natures de valeurs

- **Paramètres (interface)** : `{}`
- **Tables / vues** : `dimension`
- **Résultat sur le corpus** : 15 ligne(s)

```sql
SELECT nature_code, grandeur_code, count(*) AS n FROM dimension GROUP BY nature_code, grandeur_code ORDER BY nature_code, grandeur_code;
```

Exemple de résultat :

```json
[
 {
  "nature_code": "autorise_exact",
  "grandeur_code": "jeu",
  "n": 13
 },
 {
  "nature_code": "autorise_exact",
  "grandeur_code": "longueur",
  "n": 9
 }
]
```
