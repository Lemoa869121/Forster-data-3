# 15. Informations difficiles à automatiser et points de contrôle humain

## Difficultés structurelles observées dans le corpus

1. **Planches en image sans texte** (EFR-21-002687 : 35 planches ; EFR-24-000553 : 65 planches). Les références exactes de **serrures** (pl. 48), contre-faces de vitrages DGU (pl. 57), sections de parcloses/joints par épaisseur, verrous thermiques (pl. 58-65) n'existent qu'en image. → Extraction visuelle obligatoire ; dans la base, les serrures concernées existent comme *types* (« serrure à mortaiser 2 points ») avec `statut_extraction = 'a_verifier'` et un `controle_humain(planche_image)`.
2. **OCR de scans anciens** : inversions de colonnes, chiffres collés, « E160 » pour « EI 60 », « 6 » pour « G » (main gauche). Les tableaux de classement (§3.2 de 11-A-507, §4.2 de 13-A-704) et les tableaux multi-colonnes de dimensions sont les plus touchés.
3. **Tableaux à formats alternatifs** (« OU », portrait/paysage, plusieurs colonnes MAXIMALE) : l'association largeur ↔ hauteur ↔ surface doit être confirmée sur l'original.
4. **Documents compilés** : la pagination est celle de chaque document, pas du PDF ; un même PDF contient jusqu'à 6 documents.
5. **Références de plages** (« 936.809 à 936.817 », « 948003 à 948010 ») : non éclatées automatiquement (on ne déduit pas l'existence de références intermédiaires).
6. **Codes de fonction de serrure** (W, E, B, D, L+W) : non définis dans les PV ; à documenter via la nomenclature Forster (enrichissement) sans jamais les réinterpréter dans les données document.
7. **Clair vs hors-tout**, **passage libre vs vantail hors-tout** : grandeurs non comparables, à ne pas confondre dans les filtres.
8. **Conditions de combinaison** en langage naturel (« si et seulement si… », « non cumulable sauf mention ») : stockées en `restriction` lisible ; leur traduction en règles automatiques est une étape ultérieure à valider.
9. **Documents cités non fournis** (18/1, 18/2, PV de cloisons support, appréciations de laboratoire) : la base trace leur existence mais ne peut rien affirmer de leur contenu.

## Points de contrôle à chaque import

| # | Contrôle | Requête d'aide |
|---|---|---|
| 1 | Classement(s) relus sur l'original, y compris présence de C, S, I1/I2 | `SELECT * FROM v_classement_feu WHERE document_id = ?` |
| 2 | Validité effective = dernière reconduction (et extensions non reconduites) | Q12, Q08 |
| 3 | Lignes `statut_extraction IN ('ocr_degrade','a_verifier')` | `SELECT * FROM v_composant WHERE statut_extraction <> 'extrait'` |
| 4 | Tableaux de serrures : kit/coffre/gâche/fonction/DIN/AP ligne à ligne | Q02 |
| 5 | Dimensions : formats alternatifs, unités, testé vs autorisé | Q20, `v_dimension` |
| 6 | Sens du feu par vitrage / équipement | `restriction` type `sens_feu` |
| 7 | Règles de cumul des extensions | `document_relation` `*_cumulable_avec` |
| 8 | Enrichissements `a_verifier` avant affichage public | `SELECT * FROM enrichissement_externe WHERE statut_fiabilite_code = 'a_verifier'` |
| 9 | Clôture des `controle_humain` | Q15 |

## État actuel
32 points ouverts sur les 6 fichiers : liste générée dans [`13b_CONTROLES_OUVERTS.md`](13b_CONTROLES_OUVERTS.md).
