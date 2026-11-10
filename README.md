# Base PV Forster — résistance au feu (SQLite + sql.js, 100 % statique)

Base de données de référence des procès-verbaux de classement, reconductions et extensions (marché français) des systèmes acier **Forster**, conçue pour une application de recherche/filtrage hébergée sur **GitHub Pages** : la base est un fichier SQLite versionné, interrogé dans le navigateur par **sql.js** (WebAssembly), sans aucun serveur.

État : **6 PDF analysés** (17 documents logiques + 21 documents cités), 630 occurrences de composants atomisées, 359 références, 327 limites dimensionnelles, 17 classements, 32 points de contrôle humain ouverts.

## Démarrage

```bash
python3 scripts/build_db.py      # régénère db/forster_pv.sqlite depuis data/sources/ (Python 3 standard, aucune dépendance)
python3 scripts/test_queries.py  # exécute les 20 requêtes de référence
python3 scripts/export_json.py   # exports JSON (un fichier par table + global)
python3 scripts/gen_docs.py      # dictionnaire, référentiels, requêtes, contrôles
python3 -m http.server 8000      # puis http://localhost:8000/app/
```
GitHub Pages : Settings → Pages → *Deploy from branch* `main` / racine. L'application est servie sous `/app/`.

## Contenu

| Dossier | Rôle |
|---|---|
| `db/schema.sql` | Schéma SQLite complet (tables, contraintes, 59 index, 6 vues) |
| `db/referentiels.sql` | Listes de valeurs contrôlées (31 tables `ref_*`) |
| `db/forster_pv.sqlite` | Base générée, servie à l'application |
| `data/sources/` | **Source de vérité** : JSON par PDF + catalogue partagé |
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

## Règles de données (appliquées par le schéma)
- Valeur testée ≠ limite autorisée (`nature_code` obligatoire ; `essai_resultat` = testé uniquement).
- Donnée document ≠ donnée externe (`enrichissement_externe`, `source='enrichissement'`, statut `confirme` / `a_verifier`) ; l'enrichissement ne peut pas créer d'autorisation.
- Références et unités conservées telles qu'écrites + colonnes normalisées.
- Chaque donnée pointe vers sa page / section / planche (`source_page`) ; absence = `NULL` ou `non_trouve`, jamais chaîne vide.
- Les PDF sources ne sont pas versionnés (liens Drive dans `fichier_source`).

> Ces données décrivent le contenu des PV ; elles ne valent pas avis de conformité. Seul le PV original, accompagné de ses reconductions en cours de validité, fait foi.
