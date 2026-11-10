# 14. Plan d'import des ~100 documents (flux local → commit GitHub)

## Principe
La source de vérité est `data/sources/` (JSON lisible, diffable). La base SQLite est un **artefact régénéré**. Un PDF source = un fichier `data/sources/documents/<FIC-ID>.json` ; les entités partagées sont dans `catalogue.json`.

## Étapes pour chaque PDF

1. **Identifier le fichier** : `fichier_source` (nom exact, id Drive, taille, date) ; découper le PDF en documents logiques (reconduction, PV, extensions…) dans l'ordre → `document.ordre_dans_fichier`.
2. **Extraire le texte** : PDF natif → texte direct ; scan → OCR ; noter la qualité par document (`statut_extraction`).
3. **Pages sources** : créer les `source_page` au fil de la lecture (page selon la pagination du document, section, planche, type de zone).
4. **Ordre de remplissage** (identique à `build_db.py`) :
   1. catalogue : `organisme` (+ alias), `intervenant`, `norme`, `systeme`, `reference_composant`
   2. `fichier_source` → `document` (y compris les documents cités, `present_dans_corpus = 0`)
   3. `source_page` → `document_relation` → `document_organisme`, `document_signataire`, `document_norme`, `document_systeme`
   4. `configuration` (une par variante classée) → `performance` + `perf_<domaine>`
   5. `document_composant` (parents puis enfants) → `dc_*`, `caracteristique_document`
   6. `dimension_format` → `dimension`
   7. `support_pose`, `restriction`, `controle_humain`
   8. `essai`, `essai_resultat`, `document_essai`, `reference_alias`, `enrichissement_externe`
5. **Build + tests** : `build_db.py` (refuse toute violation FK/CHECK/UNIQUE et toute chaîne vide) puis `test_queries.py`.
6. **Relecture humaine** des lignes `statut_extraction <> 'extrait'` et des `controle_humain` ouverts (voir doc 15).
7. **Commit** : un commit par PDF (`data: 13-A-175 + ext 14/1`), `db/` + `data/` + `docs/` régénérés ensemble.

## Gestion des doublons

| Cas | Règle |
|---|---|
| Même référence dans plusieurs documents | Une seule ligne `reference_composant` (clé `(fabricant_id, reference_normalisee)`), N lignes `document_composant` |
| Même référence écrite différemment (« 948.002 » / « 948002 », « TS93 » / « TS 93 ») | Normalisation : majuscules, suppression espaces et points → même référence ; écriture d'origine dans `reference_brute` (+ `reference_alias` si utile) |
| Ancienne / nouvelle référence (917611 ex-907642) | Deux écritures → une référence + `reference_alias(type='ancienne_reference')` |
| Même organisme sous plusieurs raisons sociales | Un `organisme` + `organisme_alias` ; `document_organisme.nom_tel_qu_ecrit` conserve l'écriture |
| Même document présent dans deux PDF (ex. une extension multiple jointe à plusieurs PV) | Même `document.id` : le second fichier ne crée pas de ligne, il référence l'id (le build échoue sur doublon de clé → détection automatique) |
| Document cité puis fourni plus tard | La ligne existante (`present_dans_corpus = 0`) est complétée : `present_dans_corpus = 1`, `fichier_source_id`, dates… même `id` |
| Variantes proches (verrou thermique 11-A-507 vs EFR-24-000553) | **Jamais fusionnées** : lignes distinctes, éventuel `controle_humain(incoherence)` |

## Gestion des mises à jour

| Événement | Action |
|---|---|
| Nouvelle reconduction | Nouveau `document` (reconduction) + relations `reconduit` / `reconduit_extension` / `non_reconduit` ; la vue recalcule la validité effective |
| Nouvelle révision d'un PV | Nouveau `document` (même `numero_normalise`, `revision` incrémentée) + relation `remplace` ; l'ancienne reste (historique) avec `present_dans_corpus` selon disponibilité |
| Nouvelle extension | Nouveau `document` + `etend` vers chaque PV visé + règles de cumul ; composants avec `statut_autorisation_code` (`remplacant`, `remplace`…) |
| Correction après relecture | Modifier la ligne JSON, passer `statut_extraction` à `extrait`, `controle_humain.statut = 'resolu'` + `resolution` |
| PV échu non reconduit | Rien à supprimer : `v_validite_effective` le classe hors validité |

## Outillage recommandé pour passer à 100 documents
- Script d'extraction semi-automatique (Claude ou autre) qui produit directement le JSON au format `data/sources/documents/*.json` (le format est exactement celui des colonnes, donc vérifiable par `build_db.py`).
- Pour les planches image (PV récents) : extraction visuelle page par page (OCR image / lecture assistée), saisie des tableaux de références dans le même JSON.
- Garder les ID déterministes : `DOC-<numero_normalise>`, `CFG-<doc>-<code>`, `DC-<doc>-NNNN` (numérotation stable une fois commitée).
