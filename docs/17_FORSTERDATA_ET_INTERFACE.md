# 17 — Intégration de ForsterData et interface v3

Source d'inspiration et de données : https://lemoa869121.github.io/forsterdata/ (dépôt public `Lemoa869121/forsterdata`, export Glide du 2026-11-06, copié dans `data/sources/forsterdata/data.json`).

## 1. Données : une couche Forster distincte

| Catégorie | Fiches | Rapprochées au corpus (exact / partiel) |
|---|---|---|
| Feu | 179 | 171 / 0 |
| Anti-effraction | 66 | 10 / 26 |
| Pare-balles | 20 | 14 / 4 |
| AEV | 68 | 8 / 49 |
| Acoustique | 131 | 36 / 15 |

* Table `fiche_forsterdata` : une ligne par fiche, avec toutes les colonnes publiées dans `details_json`. Les fiches sont rattachées au pseudo-document `DOC-FORSTERDATA` (type `synthese_fabricant`), jamais aux PV eux-mêmes. Le PV ou rapport du corpus reconnu par son numéro est dans `document_pv_id`, avec le niveau de rapprochement `exact` / `partiel` / `non_trouve`.
* Table `lien_forsterdata` : 471 liens de cumul Feu ↔ RC ↔ FB, calculés avec la règle de ForsterData. Il faut la même série, la même famille d'ouvrage (portes regroupées, ouvrant, cloison, cloison bords-à-bords, mur rideau…) et une déclaration dans « Cumul de perf ». Si les deux fiches déclarent, la plus spécifique fait foi (FB > RC > Feu).
* 57 cumuls dédoublonnés par système, typologie et classes sont ajoutés à `cumul_performance` (statut `declare_fabricant`).
* Contrôle croisé : 17 fiches dont la classe diffère de celle lue dans le document rapproché donnent un `controle_humain` de type `incoherence`. Parmi elles, 08-10-A287-B1 (RC3 selon ForsterData, RC2 selon le dossier de rangement) et cinq PV feu dont la classe E30/E60 diffère.
* Régénération : `python3 scripts/build_db.py && python3 scripts/import_forsterdata.py && python3 scripts/build_db.py`.

## 2. Interface (reprise des principes de ForsterData)

* Sélecteur de performances groupé (Sécurité : Feu, Anti-effraction, Pare-balles ; Performances : AEV, Acoustique, Rapports d'essais), avec le nombre d'éléments.
* Filtres propres à chaque catégorie :
  * Feu : moteur SQL existant, plus « Cumul déclaré (ForsterData) » ;
  * RC / FB : classe, application, série, cumul avec les autres catégories ;
  * AEV : minimums A / E / V ;
  * Acoustique : Rw minimum ;
  * Rapports : domaine, système, typologie, type, laboratoire ;
  * case « Document retrouvé dans le corpus PDF ».
* Tableau triable par colonne, pagination de 25, colonne « Cumul RC / FB » ou « Cumul feu / FB », colonne Corpus (✓ / ≈ / ⚠ écart / —).
* Tiroir de détail :
  * fiche ForsterData : performances cumulées cliquables, document du corpus et éventuelles incohérences, dimensions, toutes les rubriques ;
  * PV : onglets existants, plus le bloc « Performances cumulées (ForsterData) ».
* Comparaison côte à côte de 2 à 4 éléments, avec l'option « uniquement les différences ».
* Adresse directe par catégorie et filtres : `#cat=rc&f={…}`, `#cat=feu&systeme=…`. Les liens courts `#rc`, `#aev` sont acceptés.

## 3. Différences assumées avec ForsterData

* Les PV feu restent ceux du corpus PDF (112 PV et leurs extensions), avec la page source de chaque donnée. Les fiches feu de ForsterData servent aux liens de cumul et au contrôle croisé.
* Un lien de cumul ForsterData reste une déclaration du fabricant : il ne remplace pas la vérification que la même construction est couverte par les deux documents.
