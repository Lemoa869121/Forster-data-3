# 8. Mécanisme d'enrichissement externe

## Règles (appliquées par le schéma, pas seulement par convention)

| Règle | Mécanisme |
|---|---|
| Donnée externe toujours séparée | Table dédiée `enrichissement_externe` ; aucune autre table n'accepte de source externe |
| Colonne de source | `source TEXT NOT NULL DEFAULT 'enrichissement' CHECK (source = 'enrichissement')` + `source_libelle`, `source_url`, `date_recherche` |
| Statut de fiabilité | `statut_fiabilite_code` → `ref_statut_fiabilite` (`confirme`, `a_verifier`) |
| Ne jamais écraser une donnée document | Pas de colonne partagée ; la vue `v_reference_fiche` juxtapose `source='document'` et `source='enrichissement'` |
| Ne jamais étendre performance / compatibilité / conformité | L'enrichissement est rattaché à `reference_composant` (le catalogue), **jamais** à `document_composant`, `performance`, `dimension_format` ni `configuration` : une donnée externe ne peut donc pas créer une autorisation dans un PV |

Statut `confirme` : uniquement quand la source est le fabricant (brochure / fiche technique officielle). Source distributeur, revendeur ou marketplace → `a_verifier`.

## Exemple réel (recherche du 2026-11-10)

| Référence | Caractéristique | Valeur | Statut | Source |
|---|---|---|---|---|
| HZ43F (DORMA) | fonction | Verrouillage automatique du battant semi-fixe | confirme | brochure technique dormakaba HZ 43-F |
| HZ43F | main | DIN-L ou DIN-R (pas de modèle universel) | confirme | idem |
| HZ43F | position | Montage en haut | confirme | idem |
| HZ43F | gamme | Variantes HZ 43-F22 / HZ 43-F24 | confirme | Technikprospekt dormakaba |
| TS93 (DORMA) | type / force / norme | Glissière à came ; EN 2–5 ou EN 5–7 ; NF EN 1154 | confirme | brochure dormakaba TS 93 |
| TS5000 (GEZE) | force / norme / largeur | EN 2–6 ; EN 1154 ; vantail ≤ 1400 mm | a_verifier | distributeurs |
| 118 profix 2 (EFF EFF) | type / réversible | Gâche à émission, FaFix 3 mm ; symétrique DIN G/D | a_verifier | fiches effeff hébergées par distributeurs |

Points de vigilance tracés dans `commentaire` : la largeur de vantail 1400 mm annoncée pour le TS 5000 **ne modifie pas** le domaine du PV (vantail ≤ 1460 mm dans EFR-24-000553 : le PV prime, l'enrichissement ne dit rien de la compatibilité). Un revendeur indique qu'une variante 118.14 n'est « pas homologuée portes coupe-feu » : l'enrichissement le signale mais ne restreint ni n'autorise rien.

```sql
-- Fiche HZ43F : occurrences document + enrichissement, séparés
SELECT source, caracteristique, valeur, statut_fiabilite, origine FROM v_reference_fiche WHERE reference_normalisee = 'HZ43F';
```

## Procédure d'enrichissement (répétable)

1. Lister les références candidates : `SELECT rc.* FROM reference_composant rc LEFT JOIN enrichissement_externe e ON e.reference_id = rc.id WHERE e.id IS NULL AND rc.fabricant_id <> 'ORG-FORSTER'` (puis les références Forster).
2. Rechercher en priorité la documentation fabricant (fiche technique, brochure, déclaration de performance).
3. Saisir dans `data/sources/catalogue.json` → `enrichissement_externe` : une ligne par attribut atomique, unité normalisée, URL et date.
4. `confirme` seulement si la source est le fabricant et que la référence correspond exactement ; sinon `a_verifier`.
5. Régénérer la base (`scripts/build_db.py`) et committer.

L'application affiche les données enrichies dans un bloc distinct (« Informations fabricant — hors PV ») avec le badge de fiabilité, et ne les utilise jamais comme critère de conformité.
