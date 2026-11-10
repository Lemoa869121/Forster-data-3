# 3. Inventaire des données filtrables (atomisées et typées)

Légende — **Nature** : T = valeur testée, A = limite autorisée, C = caractéristique de composant, M = métadonnée. **Origine** : D = document, E = enrichissement externe. **Usage** : F = filtre, R = recherche, I = information. Le dictionnaire exhaustif (toutes colonnes, contraintes, exemples réels) est généré dans [`04_DICTIONNAIRE_CHAMPS.md`](04_DICTIONNAIRE_CHAMPS.md).

## 3.1 Identification du document
| Champ | Définition | Type | Unité | Nat. | Orig. | Usage | Valeurs contrôlées |
|---|---|---|---|---|---|---|---|
| document.numero | N° tel qu'écrit (« 08 - A - 275 », « 22/2 - Révision 1 ») | TEXT | — | M | D | R | — |
| document.numero_normalise | « 08-A-275 », « 11-A-507/EXT-22/2 » | TEXT | — | M | D | F,R | règle de normalisation |
| document.revision | Indice | TEXT | — | M | D | F | — |
| document.type_code | Nature du document | TEXT | — | M | D | F | `ref_type_document` |
| document.date_emission / date_validite | Dates ISO | TEXT | date | M | D | F | AAAA-MM-JJ (CHECK GLOB) |
| document.validite_liee_au_pv | Extension sans date propre | INTEGER | 0/1 | M | D | F | — |
| v_validite_effective.date_validite_effective | Validité après reconductions | TEXT | date | M | calcul | F | — |
| document.numeros_affaire | Affaires Efectis | TEXT | — | M | D | R | liste « ; » |
| document.present_dans_corpus | Cité mais non fourni | INTEGER | 0/1 | M | D | F | — |
| fichier_source.* | Nom, id Drive, taille, codes du nom de fichier | TEXT/INT | — | M | D | F,I | — |

## 3.2 Organismes et intervenants
| Champ | Définition | Type | Valeurs |
|---|---|---|---|
| document_organisme.role_code | laboratoire, demandeur, co_demandeur, fabricant_ossature, fabricant_vitrage | TEXT | `ref_role_organisme` |
| organisme.nom_normalise / alias | Raison sociale normalisée + variantes écrites (« FORSTER ROHR & PROFILTECHNIK AG »…) | TEXT | `organisme_alias` |
| organisme.pays_code, ville | Localisation (usine de production) | TEXT | ISO 3166 |
| document_signataire.fonction | Chargé d'affaires, superviseur… | TEXT | — |

## 3.3 Référentiel normatif et essais
| Champ | Définition | Type | Nat. |
|---|---|---|---|
| norme.code / annee / amendement | « EN 13501-2 » / « 2016 » ; « EN 1634-1 » / « +A1:2018 » | TEXT | M |
| document_norme.role / paragraphe | classement (§7.5.2, §7.5.5), essai, exclusion | TEXT | M |
| essai.reference, laboratoire, date, objet, système testé | Essais cités en justification | TEXT | M |
| essai_resultat.critere_code / duree_min / operateur | E 31 min, W 14 min, « plus de 60 » (`gt`) | TEXT/REAL | **T** |

## 3.4 Produit, système, configuration
| Champ | Définition | Type | Valeurs |
|---|---|---|---|
| systeme.nom_normalise | PRESTO 50, PRESTO 60, FUEGO LIGHT 30, FUEGO LIGHT 60, THERMFIX VARIO | TEXT | table `systeme` |
| systeme.isolation_thermique / profondeur_mm | | INTEGER/REAL | — |
| document_systeme.role | principal, variante, support_associe, integration | TEXT | CHECK |
| configuration.typologie_code | bloc_porte, cloison_vitree, cloison_vitree_bord_a_bord, facade_vitree | TEXT | `ref_typologie` |
| configuration.nb_vantaux_min/max, vantaux_inegaux, vitree | | INTEGER | — |
| configuration.parent_configuration_id | Variante d'une configuration | TEXT | — |

## 3.5 Performances
| Champ | Définition | Type | Nat. |
|---|---|---|---|
| performance.domaine_code | feu (puis effraction, balistique, aev, acoustique) | TEXT | M |
| performance.libelle_tel_qu_ecrit / classe_normalisee | « E I2 30 » / « EI2 30 » | TEXT | A (classement) |
| perf_feu.critere_e/i/w/m/c/s, variante_i (I, I1, I2), classe_c | Atomisation EN 13501-2 | INTEGER/TEXT | A |
| perf_feu.duree_min | 15…240 (CHECK) | INTEGER | A |
| restriction(type `sens_feu`) | Sens du feu (indifférent / côté opposé / tampon…) | TEXT | A |

## 3.6 Dimensions et limites géométriques (testé ≠ autorisé)
| Champ | Définition | Type | Unité | Valeurs |
|---|---|---|---|---|
| dimension_format.objet_code | passage_libre, vantail_hors_tout, vitrage_hors_tout, vitrage_clair, vitrage_forme, panneau, cloison, facade_entre_dalles, imposte, allege, ensemble, jeu_*, prise_feuillure, empenage, film_adhesif, plinthe, angle_vitrages… | TEXT | — | `ref_objet_dimension` |
| dimension_format.groupe_alternative / orientation | Formats « OU », portrait/paysage | TEXT | — | — |
| dimension.grandeur_code | largeur, hauteur, surface, epaisseur, angle, diametre, longueur, jeu, pas | TEXT | — | `ref_grandeur` |
| dimension.nature_code | autorise_max, autorise_min, autorise_exact, teste, nominal, exige_min | TEXT | — | `ref_nature_valeur` |
| dimension.operateur_code | le, lt, ge, gt, eq | TEXT | — | `ref_operateur` |
| dimension.valeur_origine / unite_origine | Tel qu'écrit (« 4,54 m² », « sans limite ») | TEXT | origine | — |
| dimension.valeur_norm / unite_norm_code | Valeur normalisée filtrable | REAL | mm, m2, deg, um | `ref_unite` |
| dimension.sans_limite | « sans limite / illimitée » | INTEGER | — | CHECK cohérent avec valeur_norm |
| dimension.tolerance_plus/moins | ex. seuil 10 (+3/−5) | REAL | mm | — |

## 3.7 Vitrages et remplissages (`dc_vitrage`)
gamme (PYROSWISS, CONTRAFLAM LITE, CONTRAFLAM STRUCTURE, PYROGUARD T, PYROSTOP, POLFLAM/FIREFLAM, VETROFLAM) · designation · type_vitrage_code (monolithique, feuilleté, isolant, triple, isolant_store, angle_corner, isolant_angle) · epaisseur_mm / min / max · classe_nominale (affichée dans le nom commercial, **pas** une performance) · intercalaire_min/max_mm · composition_detaillee_disponible (0 = « en possession du laboratoire »). Panneaux : `document_composant(categorie='panneau')` + surfaces dans `dimension_format`. Films : `film_adhesif` + limites.

## 3.8 Quincaillerie jusqu'à la référence et la fonction
| Table | Attributs atomiques |
|---|---|
| `dc_serrure` | type_serrure_code (mortaiser, solénoïde, rouleau, commande_levier, commande, crémone_levier, crémone_pompier, verrou_automatique, verrou_thermique, verrou_bascule, non_verrouillé) · fonction_code (W, E, B, D, L+W — codes Forster, signification **non définie par les PV**) · nb_points · point_haut/médian/bas · antipanique · main_din (G/D) · entraxe_mm · type_commande (mécanique, électrique, motorisée, DAS électrique, thermique) · version (classique / push_bar) · seuil_temperature_c · position_depuis_bas/haut_mm · vantail (unique/principal/secondaire) |
| `document_composant.parent_id` + `role_dans_parent` | Composition kit → coffre / gâche / coffre_principal / coffre_secondaire / pêne |
| `dc_articulation` | type (paumelle, pion anti-dégondage, bras pivot, pivot de sol) · mode_fixation (souder, visser, encastrer, sceller) · réglage (2D/3D) · distance_extremite_mm · position |
| `dc_ferme_porte` | type (applique, encastré, ouvre-porte) · cote_feu_autorise · cote_oppose_autorise · protection_requise · force_en · largeur/poids/angle max |
| `dc_joint` | type (intumescent, EPDM, CR, fibre minérale, fibre céramique, butée) · largeur · épaisseur (ou plage min-max) · position (fond de feuillure, ailette, parclose, battement, tranche) · marque_produit |
| `dc_profile` | série (système) · largeur × profondeur · isolé · hauteur_max_emploi · restriction côté feu |
| `dc_fixation` | type (vis béton, vis+cheville, goujon…) · diamètre · longueur · pas max · distance aux angles · support cible |
| `caracteristique_document` | Toute autre caractéristique typée (section, conditionnement, plage de longueur de push-bar, réglable…) |
| `document_composant` (commun) | reference_brute (tel qu'écrit) · reference_normalisee (via `reference_composant`) · fabricant · catégorie · rôle · localisation (huisserie, vantail principal/secondaire…) · statut_autorisation (autorisé, obligatoire, interdit, remplacé, remplaçant) · condition_texte · statut_extraction |

## 3.9 Mise en œuvre, supports, domaine d'application, restrictions
`support_pose` : type_support_code (béton armé, béton plein/parpaing, béton cellulaire, maçonnerie homogène, cloison 98/48, 120/70, cloison vitrée associée, poteau acier protégé, dalle) · masse_vol_min + opérateur · epaisseur_min + opérateur · classement_pv_exige (« EI 60 ») · prolongation / imposte / allège autorisées · pas_fixation_max. `restriction` : type (sens_feu, cumul_extensions, interdiction, condition_mise_en_oeuvre, condition_combinaison, condition_vitrage, exclusion_normative, limitation_validite) + libellé filtrable + extrait source.

## 3.10 Traçabilité
`source_page` (document, page selon pagination du document, total, section, planche, type de zone : page de garde / texte / tableau / planche / suivi de révision) ; chaque ligne de donnée pointe sur une `source_page`. `statut_extraction` (extrait, ocr_degrade, a_verifier, non_trouve) sur documents, composants, formats, dimensions, performances. `controle_humain` pour chaque ambiguïté.

## 3.11 Enrichissement (origine E)
`enrichissement_externe` : reference_id · type_caracteristique_code · valeur (texte/num/bool) · unité · `source = 'enrichissement'` (CHECK) · source_libelle · source_url · date_recherche · statut_fiabilite (confirme / a_verifier). Voir [`06_ENRICHISSEMENT.md`](06_ENRICHISSEMENT.md).
