# Base PV Forster — résistance au feu (SQLite + sql.js, 100 % statique)

Base de données de référence des procès-verbaux de classement, reconductions et extensions (marché français) des systèmes acier **Forster**, conçue pour une application de recherche/filtrage hébergée sur **GitHub Pages** : la base est un fichier SQLite versionné, interrogé dans le navigateur par **sql.js** (WebAssembly), sans aucun serveur.

État : **126 PDF** du dossier « PV FEU Forster France E-EI / PV » (112 PV de classement, 126 extensions, 102 reconductions, 6 PV DAS CNPP = 346 documents fournis, + 119 documents cités), 9 914 occurrences de composants, 1 773 références, 211 classements, 450 points de contrôle humain.

- **6 PV saisis et atomisés à la main** (11-A-507, 13-A-175, 08-A-275, 13-A-704, EFR-21-002687, EFR-24-000553).
- **120 PDF extraits automatiquement** (texte natif + OCR) : tout est marqué `a_verifier` — voir [extraction automatique](docs/14_EXTRACTION_AUTOMATIQUE.md). La validité effective calculée concorde avec la date du nom de fichier pour les 112 PV.

## Démarrage

```bash
# (optionnel) OCR + extraction automatique d'un dossier de PDF :
#   ls PV/*.pdf | xargs -d '\n' -I{} -P 2 scripts/ocr_pdf.sh "{}" ocr_txt && python3 scripts/auto_extract.py ocr_txt
python3 scripts/build_db.py      # régénère db/forster_pv.sqlite depuis data/sources/ (Python 3 standard, aucune dépendance)
python3 scripts/test_queries.py  # exécute les 20 requêtes de référence
python3 scripts/export_json.py   # exports JSON (un fichier par table + global)
python3 scripts/gen_docs.py      # dictionnaire, référentiels, requêtes, contrôles
python3 -m http.server 8000      # puis http://localhost:8000/app/
```
GitHub Pages : Settings → Pages → *Deploy from branch* `main` / racine. L'application est servie sous `/app/`.

Police Faktum : non versionnée (licence commerciale, dépôt public) — déposer les `.otf` dans `app/fonts/` pour l'affichage aux couleurs Forster ; sinon police système.

## Contenu

| Dossier | Rôle |
|---|---|
| `db/schema.sql` | Schéma SQLite complet (tables, contraintes, 59 index, 6 vues) |
| `db/referentiels.sql` | Listes de valeurs contrôlées (31 tables `ref_*`) |
| `db/forster_pv.sqlite` | Base générée, servie à l'application |
| `data/sources/` | **Source de vérité** : JSON par PDF (`AUTO-*` = extraction automatique) + catalogues `catalogue.json` (manuel) et `catalogue_auto.json` |
| `data/export/` | Export JSON (format d'échange / secours) + exemples |
| `queries/filtres.sql` | Requêtes de filtre testées (paramètres nommés sql.js) |
| `app/` | Démonstrateur statique (filtres → SQL paramétré, fiche PV) |
| `scripts/` | Build reproductible, export, tests, génération de docs |
| `docs/` | Analyse et spécifications (voir ci-dessous) |

## Documentation (format de réponse demandé)

1-2. [Analyse des documents, points communs et différences](docs/01_ANALYSE_DOCUMENTS.md)
3. [Inventaire des données filtrables](docs/02_INVENTAIRE_DONNEES.md)
4-5. [Schéma SQLite et schéma relationnel (Mermaid)](docs/03_SCHEMA_RELATIONNEL.md) · DDL : [`db/schema.sql`](db/schema.sql)
6. [Dictionnaire des champs](docs/04_DICTIONNAIRE_CHAMPS.md) (généré)
7. [Référentiels contrôlés](docs/05_REFERENTIELS.md) (généré)
8. [Enrichissement externe](docs/06_ENRICHISSEMENT.md)
9. [Documents liés](docs/07_DOCUMENTS_LIES.md)
10. [Extension effraction / balistique / AEV / acoustique](docs/08_EXTENSION_DOMAINES.md)
11. [Requêtes SQL de filtre + résultats réels](docs/09_REQUETES_FILTRES.md) (généré)
12. [Architecture statique, dépôt, régénération, versionnement](docs/10_ARCHITECTURE_STATIQUE.md)
13. [Exemple d'extraction atomisée](docs/11_EXEMPLE_EXTRACTION.md)
14. [Plan d'import des ~100 documents](docs/12_PLAN_IMPORT.md)
15. [Points de contrôle humain](docs/13_CONTROLES_HUMAINS.md) · [liste des contrôles ouverts](docs/13b_CONTROLES_OUVERTS.md)
16. [Extraction automatique du corpus complet](docs/14_EXTRACTION_AUTOMATIQUE.md)
17. [Interface, charte Forster et filtres](docs/15_FILTRES_ET_INTERFACE.md)

## Règles de données (appliquées par le schéma)
- Valeur testée ≠ limite autorisée (`nature_code` obligatoire ; `essai_resultat` = testé uniquement).
- Donnée document ≠ donnée externe (`enrichissement_externe`, `source='enrichissement'`, statut `confirme` / `a_verifier`) ; l'enrichissement ne peut pas créer d'autorisation.
- Références et unités conservées telles qu'écrites + colonnes normalisées.
- Chaque donnée pointe vers sa page / section / planche (`source_page`) ; absence = `NULL` ou `non_trouve`, jamais chaîne vide.
- Les PDF sources ne sont pas versionnés (liens Drive dans `fichier_source`).

> Ces données décrivent le contenu des PV ; elles ne valent pas avis de conformité. Seul le PV original, accompagné de ses reconductions en cours de validité, fait foi.

## Rapports d'essais et cumuls de performances (v1.3.0)

272 rapports d'essais du dossier « Rapports d'essais » (effraction, pare-balles, explosion, AEV, acoustique, chocs, endurance, issues de secours, thermique, classement feu EN 13501-2) sont intégrés (`DOC-RAP-*`, extraction automatique à relire).
Les cumuls **énoncés** (synthèse Forster 16/05/2024, rapports portant deux classes, éprouvettes coupe-feu) sont dans `cumul_performance`.
Le rapprochement système × typologie se trouve dans `v_cumul_potentiel` ; ce n'est pas un cumul certifié. Voir [docs/16_RAPPORTS_ESSAIS_ET_CUMULS.md](docs/16_RAPPORTS_ESSAIS_ET_CUMULS.md).
Régénération : `scripts/ocr_rapport.sh` (texte par page) puis `python3 scripts/extract_rapports.py <dossier_txt>` et `python3 scripts/build_db.py`.

## Base ForsterData et interface v3 (v1.4.0)

La base ForsterData (fiches Feu, RC, FB, AEV, Acoustique saisies par Forster) est importée comme couche distincte (`fiche_forsterdata`, `lien_forsterdata`), rapprochée des PV et rapports du corpus et contrôlée contre eux.
L'interface reprend ses principes : sélecteur de performances, tableaux triables, tiroir de détail, comparaison de 2 à 4 éléments, liens Feu ↔ RC ↔ FB. Voir [docs/17_FORSTERDATA_ET_INTERFACE.md](docs/17_FORSTERDATA_ET_INTERFACE.md).
