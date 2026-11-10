# 10. Extension du socle : effraction, balistique, AEV, acoustique

## Ce qui ne change pas
`fichier_source`, `document`, `document_relation`, `organisme`, `norme`, `essai`, `systeme`, `configuration`, `reference_composant`, `document_composant`, `dc_*`, `dimension_format`, `support_pose`, `restriction`, `source_page`, `enrichissement_externe`, `controle_humain` sont **communs à tous les domaines**. Un PV d'effraction RC3 sur une porte Forster utilise les mêmes profilés, serrures et paumelles (mêmes `reference_composant`) qu'un PV feu : le filtre « serrure 907724 » trouvera les deux.

## Ce qui est ajouté par domaine
1. une valeur dans `ref_domaine_performance` (déjà présentes : `effraction`, `balistique`, `aev`, `acoustique`) ;
2. une table de détail 1:1 avec `performance` (déjà créées, vides) :

| Domaine | Table | Colonnes | Norme typique |
|---|---|---|---|
| effraction | `perf_effraction` | classe_rc (RC1…RC6, CHECK), norme_id, duree_resistance_min | EN 1627 |
| balistique | `perf_balistique` | classe (FB1-FB7 / BR1-BR7), avec_eclats (S/NS), arme_munition, norme_id | EN 1522 / EN 1063 |
| AEV | `perf_aev` | classe_air, classe_eau, classe_vent, pressions (Pa), norme_id | EN 14351-1 / EN 12207-12208-12210 |
| acoustique | `perf_acoustique` | rw_db, c_db, ctr_db, norme_id | EN ISO 10140 / 717-1 |

3. si nécessaire, des valeurs supplémentaires dans `ref_objet_dimension` (ex. `eprouvette`), `ref_type_restriction`, `ref_critere_*` ; et pour les essais, des `essai_resultat` avec un critère du domaine (ajouter une table `ref_critere_<domaine>` ou généraliser `critere_code`).

## Exemple : ajout d'un PV d'effraction RC2
```sql
INSERT INTO document (id, numero, numero_normalise, type_code, domaine_code, ...) VALUES ('DOC-XXX', ..., 'rapport_classement', 'effraction', ...);
INSERT INTO configuration (...);                                   -- même table
INSERT INTO performance (id, document_id, configuration_id, domaine_code, libelle_tel_qu_ecrit, classe_normalisee)
VALUES ('PRF-XXX-0001', 'DOC-XXX', 'CFG-XXX-P1', 'effraction', 'RC 2', 'RC2');
INSERT INTO perf_effraction (performance_id, classe_rc, norme_id) VALUES ('PRF-XXX-0001', 'RC2', 'NRM-EN-1627-2011');
INSERT INTO document_composant (...);                               -- références partagées avec les PV feu
```
Requêtes multi-domaines : `SELECT * FROM performance p LEFT JOIN perf_feu f USING(performance_id) LEFT JOIN perf_effraction e ON e.performance_id = p.id …` ou une vue `v_classement_<domaine>` par domaine, sur le modèle de `v_classement_feu`.

> Note : le PV 13-A-704 montre des « mesures supplémentaires RC2/RC3 » en planches. Sans classement prononcé, **aucune** ligne `perf_effraction` n'est créée (contrôle humain tracé).

## Procédure de régénération après ajout d'une table de domaine
1. Écrire la migration `db/migrations/NNN_<description>.sql` (CREATE TABLE + index) **et** reporter la table dans `db/schema.sql` (la source de vérité pour une reconstruction complète).
2. Incrémenter `SCHEMA_VERSION` dans `scripts/build_db.py` : mineure si ajout pur (tables/colonnes nullable), **majeure** si renommage/suppression.
3. Ajouter la table à `ORDER_DOCS_2` dans `scripts/build_db.py` (ordre des clés étrangères).
4. `python3 scripts/build_db.py && python3 scripts/test_queries.py && python3 scripts/export_json.py && python3 scripts/gen_docs.py`.
5. Committer `db/`, `data/`, `docs/` ensemble. Si version majeure : mettre à jour `SCHEMA_MAJOR_ATTENDUE` dans `app/js/db.js` dans le **même commit**.
