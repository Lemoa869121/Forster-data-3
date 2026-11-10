# 13. Exemple d'extraction atomisée (conforme au schéma)

Toute la base est un exemple réel : les 6 PDF ont été extraits dans `data/sources/` (format = lignes par table, colonnes exactes du schéma) et régénérés dans `db/forster_pv.sqlite` et `data/export/`.

| Fichier | Contenu |
|---|---|
| [`data/sources/documents/11-A-507.json`](../data/sources/documents/11-A-507.json) … | Source éditable, un fichier par PDF |
| [`data/sources/catalogue.json`](../data/sources/catalogue.json) | Organismes, systèmes, normes, 359 références, essais, enrichissements |
| [`data/export/exemples/extension_22-2_PV_11-A-507.json`](../data/export/exemples/extension_22-2_PV_11-A-507.json) | **Un document complet, toutes tables** (extension 22/2 : verrous thermiques, serrure à rouleau, 3 essais avec valeurs testées) |
| [`data/export/exemples/PV_11-A-507_extrait.json`](../data/export/exemples/PV_11-A-507_extrait.json) | Classement + passage libre 1 vantail + kit serrure 907724 et sa composition |

## Volume extrait

| Table | Lignes | | Table | Lignes |
|---|---|---|---|---|
| document (17 fournis + 21 cités) | 38 | | document_composant | 630 |
| document_relation | 45 | | reference_composant | 359 |
| configuration | 18 | | dc_serrure | 103 |
| performance / perf_feu | 17 | | dc_profile | 88 |
| dimension_format / dimension | 174 / 327 | | dc_vitrage | 43 |
| support_pose | 32 | | dc_joint / dc_articulation / dc_ferme_porte | 44 / 39 / 41 |
| restriction | 63 | | essai / essai_resultat | 10 / 15 |
| source_page | 167 | | controle_humain | 32 |

## Extrait commenté — PV 11-A-507, bloc-porte 1 vantail

**Classement** (page 10, §3.2 — tableau illisible en OCR, classe reprise des cartouches ⇒ `a_verifier` + contrôle humain) :
```json
{"id":"PRF-11-A-507-0001","configuration_id":"CFG-11-A-507-BP","libelle_tel_qu_ecrit":"E 30 (cartouche des planches : « Classement : E 30 »)",
 "classe_normalisee":"E 30","nature_code":"classement","source_page_id":"SP-11-A-507-P010-3-2","statut_extraction":"a_verifier"}
{"performance_id":"PRF-11-A-507-0001","critere_e":1,"critere_i":0,"critere_w":0,"duree_min":30}
```
**Passage libre** (page 11, §4.3.2) — valeurs **autorisées**, « sans limite » explicite, unités d'origine conservées :
```json
{"grandeur_code":"largeur","nature_code":"autorise_max","operateur_code":"le","valeur_origine":"1610","unite_origine":"mm","valeur_norm":1610.0,"sans_limite":0}
{"grandeur_code":"surface","nature_code":"autorise_max","operateur_code":"le","valeur_origine":"4.54","unite_origine":"m²","valeur_norm":4.54,"unite_norm_code":"m2"}
{"grandeur_code":"largeur","nature_code":"autorise_min","operateur_code":"ge","valeur_origine":"sans limite","valeur_norm":null,"sans_limite":1}
```
**Kit serrure 907724** (planche 30, page 42) — référence exacte, fonction, AP, main, composition :
```json
{"id":"DC-11-A-507-0114","reference_brute":"907724","categorie_code":"kit_serrure","localisation_code":"vantail","source_page_id":"SP-11-A-507-P042-PLPLANCHE-30"}
{"document_composant_id":"DC-11-A-507-0114","type_serrure_code":"mortaiser","fonction_code":"E","nb_points":1,"point_median":1,"antipanique":1,"main_din":"G","version":"classique","vantail":"unique"}
{"id":"DC-11-A-507-0115","reference_brute":"907224","categorie_code":"coffre_serrure","parent_id":"DC-11-A-507-0114","role_dans_parent":"coffre"}
{"id":"DC-11-A-507-0116","reference_brute":"907001","categorie_code":"gache","parent_id":"DC-11-A-507-0114","role_dans_parent":"gache"}
```
**Valeurs testées** (extension 22/2, page 3) — jamais confondues avec le classement :
```json
{"essai_id":"ESS-EFR-21-002096-B","critere_code":"E","duree_min":31.0,"operateur_code":"eq","nature_code":"teste"}
{"essai_id":"ESS-EFR-21-002096-B","critere_code":"W","duree_min":14.0,"operateur_code":"eq","nature_code":"teste"}
```

## Champs non trouvés / ambiguïtés : comment c'est marqué
- Valeur absente : colonne `NULL` (jamais chaîne vide — refusée par `build_db.py`) ; si l'absence est significative : `statut_extraction = 'non_trouve'` et/ou `controle_humain(type 'non_trouve')`. Ex. seuil de température des verrous thermiques 957018/957019 (EFR-24-000553) : NULL + contrôle.
- Document cité absent : `document.present_dans_corpus = 0`, `statut_extraction = 'non_trouve'`.
- OCR douteux : `ocr_degrade` ; attribution incertaine : `a_verifier` ; incohérence : `controle_humain(incoherence)`.

## Les requêtes de l'étape 4 fonctionnent sur ces données
`python3 scripts/test_queries.py` exécute les 20 requêtes ; toutes renvoient des résultats (détail et extraits : [`09_REQUETES_FILTRES.md`](09_REQUETES_FILTRES.md), fichier brut `queries/resultats_exemple.json`). Exemples : `907724` → 11-A-507 (1 vantail et 2 vantaux) ; EI ≥ 60 → 08-A-275 et 13-A-704 ; vitrage ≥ 1500 x 2500 → 27 formats ; `TS93` + bloc-porte ≥ 30 → 11-A-507 et EFR-24-000553.
