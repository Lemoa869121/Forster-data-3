# 9. Gestion des documents liés

Table `document_relation (document_source_id, document_cible_id, type_relation_code, date_relation, commentaire, source_page_id)` + référentiel `ref_type_relation`. Sens : **source = le document qui agit** (la reconduction reconduit, l'extension étend, la révision remplace).

| type_relation_code | Source → Cible | Exemple du corpus |
|---|---|---|
| `reconduit` | reconduction → PV | 11-A-507/REC-22/2 → 11-A-507 (validité 2027-04-12) |
| `reconduit_extension` | reconduction → extension | REC-22/2 → EFR-14-000468 et EXT-22/2 |
| `non_reconduit` | reconduction → extension | 08-A-275/REC-24/3 → EXT-18/1 (« n'est pas reconduite ») |
| `etend` | extension → PV (plusieurs lignes pour une extension multiple) | EXT-MULT-EFR-22-002556 → 10-A-650, 11-A-506, 11-A-507 |
| `remplace` | nouvelle version → version remplacée | EFR-24-000553 rév. 1 → rév. 0 ; REC-22/2 rév. 1 → rév. 0 |
| `a_pour_reference` | PV → rapport / appréciation de laboratoire | 13-A-175 → 13-A-175 A et 13-A-175 B |
| `non_cumulable_avec` / `cumulable_avec` | extension → extension | EXT-22/2 non cumulable avec EFR-14-000468 ; 08-A-275 EXT-20/2 cumulable avec 18/1 |
| `support_associe` | PV → PV de la construction support | 11-A-507 → 10-A-650, 12-A-079, 12-A-077 ; EFR-24-000553 → EFR-24-000552, EFR-23-001318 |
| `revise`, `annexe_de`, `cite` | réservés | — |

**Documents cités non fournis** : créés dans `document` avec `present_dans_corpus = 0`, `statut_extraction = 'non_trouve'`, `type_code = 'document_reference'` (ou le type connu). Les relations restent complètes ; quand le document sera ajouté, sa ligne est simplement complétée (même `id`).

**Validité** : `v_validite_effective` prend la date maximale des reconductions qui ciblent le PV. Les extensions ont `validite_liee_au_pv = 1`. `v_document_rattachement` fournit, pour tout document, le(s) PV principal(aux) — c'est la jointure utilisée par l'application pour qu'un filtre « référence HZ43F » trouve le PV 11-A-507 via son extension.

```sql
-- Arbre complet autour d'un PV (requête Q08)
SELECT dr.type_relation_code, s.numero_normalise AS source, c.numero_normalise AS cible, s.date_emission, s.present_dans_corpus
FROM document_relation dr JOIN document s ON s.id = dr.document_source_id JOIN document c ON c.id = dr.document_cible_id
WHERE c.numero_normalise = '11-A-507' OR s.id IN (SELECT document_source_id FROM document_relation WHERE document_cible_id = 'DOC-11-A-507');
```

Résultat sur le corpus pour 11-A-507 : 17 relations (2 reconductions, 1 rév. remplacée, 3 extensions dont 2 multiples, 1 non-cumul, 3 supports associés, 1 rapport de référence, etc.).
