# 12. Architecture applicative statique (GitHub Pages + sql.js)

## Arborescence du dépôt

```
/
├── index.html                  # redirection vers app/ (racine GitHub Pages)
├── app/                        # application statique (aucun build requis)
│   ├── index.html              # interface de filtres + résultats + panneau détail
│   └── js/
│       ├── db.js               # chargement sql.js (CDN) + fetch .sqlite + cache + contrôle de version
│       ├── filters.js          # état des filtres -> SQL paramétré (EXISTS combinables)
│       └── app.js              # rendu UI
├── db/
│   ├── schema.sql              # DDL complet (source de vérité du schéma)
│   ├── referentiels.sql        # valeurs des tables ref_*
│   ├── migrations/             # scripts d'évolution numérotés (001_init.sql, …)
│   └── forster_pv.sqlite       # BASE GÉNÉRÉE, versionnée, servie telle quelle
├── data/
│   ├── sources/                # SOURCE DE VÉRITÉ DES DONNÉES (éditée à la main ou par script d'extraction)
│   │   ├── catalogue.json      # organismes, systèmes, normes, références, essais, enrichissements
│   │   └── documents/<fichier>.json   # un fichier par PDF source : lignes par table
│   └── export/                 # EXPORT GÉNÉRÉ
│       ├── forster_pv.json     # toute la base (format de secours de l'app)
│       ├── manifest.json       # version (sha256 des sources), nb de lignes par table
│       └── tables/<table>.json # une structure par table (colonnes + lignes)
├── queries/filtres.sql         # requêtes de référence (testées) + resultats_exemple.json
├── scripts/
│   ├── build_db.py             # sources JSON -> forster_pv.sqlite (reproductible, contrôles FK/intégrité)
│   ├── export_json.py          # sqlite -> data/export
│   ├── test_queries.py         # exécute queries/filtres.sql (échec si erreur / résultat vide)
│   └── gen_docs.py             # régénère dictionnaire, référentiels, requêtes, contrôles
└── docs/                       # analyse, schéma, plan d'import, architecture
```

Les PDF sources **ne sont pas** versionnés (confidentialité, taille) : `fichier_source.drive_file_id` / `url` pointent vers le Drive.

## Chargement au démarrage (fetch + sql.js)

```js
const SQL = await initSqlJs({ locateFile: f => `https://cdn.jsdelivr.net/npm/sql.js@1.10.3/dist/${f}` });
const version = (await (await fetch('../data/export/manifest.json', {cache:'no-cache'})).json()).meta.data_sha256.slice(0,12);
const buf = await (await fetch(`../db/forster_pv.sqlite?v=${version}`)).arrayBuffer();   // mis en Cache API par version
const db = new SQL.Database(new Uint8Array(buf));
// contrôle : meta_schema.schema_version majeure == SCHEMA_MAJOR_ATTENDUE, sinon message d'erreur
```
Taille actuelle : 1,7 Mo pour 6 PDF (≈ 0,3 Mo/PDF compilé, index compris). Projection ~100 documents : 15–30 Mo, servi compressé (gzip) par GitHub Pages ; mis en cache par version → un seul téléchargement par mise à jour. Au-delà (≫ 50 Mo), passer à `sql.js-httpvfs` (lecture par plages HTTP) sans changer le schéma.

## Des filtres de l'interface au SQL

Chaque filtre actif ajoute **une** clause `EXISTS` corrélée au PV principal via `v_document_rattachement` (donc les extensions sont prises en compte), avec un paramètre nommé :

| Filtre UI | Paramètre | Clause (abrégée) |
|---|---|---|
| Référence | `:reference` (normalisée : sans espaces ni points, majuscules) | `EXISTS(… document_composant … reference_normalisee LIKE '%'||:reference||'%' OR alias …)` |
| Système | `:systeme` | `EXISTS(… document_systeme … systeme_id = :systeme)` |
| Durée / critère | `:duree`, `:critere` | `EXISTS(… v_classement_feu … duree_min >= :duree AND critere_i = 1 …)` |
| Catégorie / fonction serrure | `:categorie`, `:fonction` | `EXISTS(… dc_serrure … fonction_code = :fonction)` |
| Largeur / hauteur ≥ | `:largeur`, `:hauteur` | `EXISTS(… dimension … nature_code='autorise_max' AND (sans_limite=1 OR valeur_norm >= :largeur))` |
| Texte libre | `:texte` (minuscules sans accents) | `EXISTS(… recherche_index … texte LIKE …)` |
| Valide au | `:valide` | `ve.date_validite_effective >= :valide` |

Les requêtes détaillées (fiche PV, composants, dimensions) sont celles de `queries/filtres.sql`. Aucune concaténation de valeur utilisateur dans le SQL : uniquement `stmt.bind()`.

Source alternative : `data/export/forster_pv.json` (ou `tables/<table>.json`) pour une page qui n'a pas besoin de SQL (ex. liste des PV), ou en secours si WebAssembly est indisponible.

## Régénération reproductible

```bash
python3 scripts/build_db.py       # supprime et recrée db/forster_pv.sqlite (schéma + référentiels + JSON) ; échoue si FK/CHECK/UNIQUE violés
python3 scripts/test_queries.py   # 20 requêtes de référence doivent s'exécuter et retourner des lignes
python3 scripts/export_json.py    # data/export/*
python3 scripts/gen_docs.py       # docs générées
git add db data docs queries && git commit -m "data: ajout PV XX-A-XXX" && git push
```
Python 3 standard uniquement (module `sqlite3`), aucune dépendance. `meta_schema.data_sha256` = empreinte des sources : deux builds des mêmes sources produisent le même contenu logique.

## Versionnement du schéma sans casser l'application

- `meta_schema.schema_version` = SemVer. **Mineure** : ajout de table/colonne nullable/vue/valeur de référentiel (l'app existante continue de fonctionner). **Majeure** : renommage/suppression/changement de sens.
- `app/js/db.js` vérifie la majeure et refuse proprement une base incompatible.
- Toute évolution = un fichier `db/migrations/NNN_*.sql` + report dans `schema.sql` + incrément de version, dans le même commit que l'adaptation éventuelle de l'app.
- Les vues (`v_*`) servent de **contrat stable** pour l'app : on peut réorganiser les tables en gardant les colonnes des vues.
- Cache : l'URL de la base contient le hash des données → pas de mélange ancienne app / nouvelle base dans le cache navigateur.
- Option : workflow GitHub Actions qui exécute `build_db.py` + `test_queries.py` sur chaque push et bloque la fusion si la base committée diffère de la base régénérée.
