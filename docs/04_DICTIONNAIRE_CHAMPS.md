# 6. Dictionnaire des champs

Généré automatiquement par `scripts/gen_docs.py` depuis `db/schema.sql` et la base. Exemple = première valeur non nulle réelle.

## `caracteristique_document` (107 lignes)

| Colonne | Type | Règle | Commentaire | Exemple |
|---|---|---|---|---|
| id | TEXT | PK |  | CAR-08-A-275-0001 |
| document_composant_id | TEXT | NOT NULL; FK → document_composant.id |  | DC-08-A-275-0018 |
| type_caracteristique_code | TEXT | NOT NULL; FK → ref_type_caracteristique.code |  | conditionnement |
| valeur_origine | TEXT | NOT NULL |  | 10 |
| valeur_texte | TEXT |  |  | Mag. 200 p. |
| valeur_num | REAL |  |  | 10.0 |
| valeur_bool | INTEGER | CHECK valeur_bool IS NULL OR valeur_bool IN (0,1) |  | 1 |
| unite_origine | TEXT |  |  | mm |
| nature_code | TEXT | NOT NULL; FK → ref_nature_valeur.code; défaut 'nominal' |  | nominal |
| source_page_id | TEXT | FK → source_page.id |  | SP-08-A-275-P012-PLPLANCHE-2 |

## `configuration` (18 lignes)

| Colonne | Type | Règle | Commentaire | Exemple |
|---|---|---|---|---|
| id | TEXT | PK |  | CFG-08-A-275-CV |
| document_id | TEXT | NOT NULL; FK → document.id |  | DOC-08-A-275 |
| code | TEXT | NOT NULL | court, unique dans le document | CV |
| libelle | TEXT | NOT NULL |  | Cloison vitrée Fuego Light 60 |
| typologie_code | TEXT | NOT NULL; FK → ref_typologie.code |  | bloc_porte |
| systeme_id | TEXT | FK → systeme.id |  | SYS-FUEGO-LIGHT-30 |
| nb_vantaux_min | INTEGER | CHECK nb_vantaux_min IS NULL OR nb_vantaux_min BETWEEN 1 AND 2 |  | 1 |
| nb_vantaux_max | INTEGER | CHECK nb_vantaux_max IS NULL OR nb_vantaux_max BETWEEN 1 AND 2 |  | 1 |
| vantaux_inegaux | INTEGER | CHECK vantaux_inegaux IN (0,1) |  | 1 |
| vitree | INTEGER | CHECK vitree IN (0,1) |  | 1 |
| parent_configuration_id | TEXT | FK → configuration.id |  | CFG-11-A-507-BP |
| source_page_id | TEXT | FK → source_page.id |  | SP-08-A-275-P001 |

## `controle_humain` (32 lignes)

| Colonne | Type | Règle | Commentaire | Exemple |
|---|---|---|---|---|
| id | TEXT | PK |  | CTL-08-A-275-0001 |
| document_id | TEXT | FK → document.id |  | DOC-08-A-275 |
| table_cible | TEXT |  |  | performance |
| ligne_id | TEXT |  |  | PRF-11-A-507-0001 |
| type_code | TEXT | NOT NULL; FK → ref_type_controle.code |  | ocr_degrade |
| description | TEXT | NOT NULL |  | §4.3.2 : valeur orpheline « 2876 » (hauteur) dans le bloc Pyrostop 60- |
| statut | TEXT | NOT NULL; défaut 'ouvert'; CHECK statut IN ('ouvert','resolu','abandonne') |  | ouvert |
| resolution | TEXT |  |  |  |
| source_page_id | TEXT | FK → source_page.id |  | SP-08-A-275-P008-4-3-2 |

## `dc_articulation` (39 lignes)

| Colonne | Type | Règle | Commentaire | Exemple |
|---|---|---|---|---|
| document_composant_id | TEXT | PK; FK → document_composant.id |  | DC-11-A-507-0074 |
| type_articulation_code | TEXT | NOT NULL; FK → ref_type_articulation.code |  | bras_pivot |
| mode_fixation | TEXT | CHECK mode_fixation IS NULL OR mode_fixation IN ('souder','visser','encastrer','sceller') |  | souder |
| reglage | TEXT | CHECK reglage IS NULL OR reglage IN ('2D','3D') |  | 2D |
| distance_extremite_mm | REAL |  |  | 120.0 |
| position | TEXT |  | 'mi_hauteur', 'haut_bas' | mi_hauteur |

## `dc_ferme_porte` (41 lignes)

| Colonne | Type | Règle | Commentaire | Exemple |
|---|---|---|---|---|
| document_composant_id | TEXT | PK; FK → document_composant.id |  | DC-11-A-507-0289 |
| type_ferme_porte_code | TEXT | NOT NULL; FK → ref_type_ferme_porte.code |  | applique |
| cote_feu_autorise | INTEGER | CHECK cote_feu_autorise IN (0,1) |  | 1 |
| cote_oppose_autorise | INTEGER | CHECK cote_oppose_autorise IN (0,1) |  | 1 |
| protection_requise | TEXT |  | ex. 'plaque PROMATECT H ou SUPALUX 10 mm' | Plaque PROMATECT H ou SUPALUX 10 mm (côté opposé au feu) |
| force_en | TEXT |  | 'EN 2-4' | EN 2-4 |
| largeur_vantail_max_mm | REAL |  |  | 1100.0 |
| poids_vantail_max_kg | REAL |  |  | 100.0 |
| angle_ouverture_max_deg | REAL |  |  | 120.0 |

## `dc_fixation` (17 lignes)

| Colonne | Type | Règle | Commentaire | Exemple |
|---|---|---|---|---|
| document_composant_id | TEXT | PK; FK → document_composant.id |  | DC-08-A-275-0032 |
| type_fixation_code | TEXT | NOT NULL; FK → ref_type_fixation.code |  | goujon |
| diametre_mm | REAL |  |  | 7.5 |
| longueur_mm | REAL |  |  | 160.0 |
| pas_max_mm | REAL |  |  | 650.0 |
| distance_angle_mm | REAL |  |  | 225.0 |
| support_cible | TEXT |  |  | Béton |

## `dc_joint` (44 lignes)

| Colonne | Type | Règle | Commentaire | Exemple |
|---|---|---|---|---|
| document_composant_id | TEXT | PK; FK → document_composant.id |  | DC-08-A-275-0008 |
| type_joint_code | TEXT | NOT NULL; FK → ref_type_joint.code |  | butee |
| largeur_mm | REAL |  |  | 45.0 |
| epaisseur_mm | REAL |  |  | 2.0 |
| epaisseur_min_mm | REAL |  |  | 2.0 |
| epaisseur_max_mm | REAL |  |  | 2.0 |
| position | TEXT | CHECK position IS NULL OR position IN ('fond_feuillure','ailette','parclose','battement','periph |  | ailette |
| marque_produit | TEXT |  | ex. 'PALSTOP P (BRANDDEX)' | PALUSOL Alu |

## `dc_profile` (88 lignes)

| Colonne | Type | Règle | Commentaire | Exemple |
|---|---|---|---|---|
| document_composant_id | TEXT | PK; FK → document_composant.id |  | DC-08-A-275-0007 |
| serie_systeme_id | TEXT | FK → systeme.id |  | SYS-FUEGO-LIGHT-30 |
| largeur_mm | REAL |  | vue (face) | 45.0 |
| profondeur_mm | REAL |  | épaisseur d'ossature | 60.0 |
| epaisseur_paroi_mm | REAL |  |  |  |
| isole_thermiquement | INTEGER | CHECK isole_thermiquement IN (0,1) |  | 1 |
| hauteur_max_emploi_mm | REAL |  | limite d'emploi énoncée (ex. 3000 pour 01.535) | 3000.0 |
| cote_feu_restriction | TEXT |  | ex. 'oppose_feu_uniquement' | oppose_feu_uniquement |

## `dc_serrure` (103 lignes)

| Colonne | Type | Règle | Commentaire | Exemple |
|---|---|---|---|---|
| document_composant_id | TEXT | PK; FK → document_composant.id |  | DC-11-A-507-0096 |
| type_serrure_code | TEXT | NOT NULL; FK → ref_type_serrure.code |  | commande |
| fonction_code | TEXT | FK → ref_fonction_serrure.code |  | B |
| nb_points | INTEGER | CHECK nb_points IS NULL OR nb_points BETWEEN 1 AND 3 |  | 1 |
| point_haut | INTEGER | CHECK point_haut IN (0,1) |  | 0 |
| point_median | INTEGER | CHECK point_median IN (0,1) |  | 1 |
| point_bas | INTEGER | CHECK point_bas IN (0,1) |  | 0 |
| antipanique | INTEGER | CHECK antipanique IN (0,1) |  | 1 |
| main_din | TEXT | CHECK main_din IS NULL OR main_din IN ('G','D','reversible') |  | D |
| entraxe_mm | REAL |  |  | 35.0 |
| type_commande | TEXT | CHECK type_commande IS NULL OR type_commande IN ('mecanique','electrique','motorisee','das_elect |  | mecanique |
| version | TEXT | CHECK version IS NULL OR version IN ('classique','push_bar') |  | classique |
| seuil_temperature_c | REAL |  |  | 124.0 |
| position_depuis_bas_mm | REAL |  |  | 490.0 |
| position_depuis_haut_mm | REAL |  |  | 120.0 |
| vantail | TEXT | CHECK vantail IS NULL OR vantail IN ('unique','principal','secondaire','tous') |  | unique |

## `dc_vitrage` (43 lignes)

| Colonne | Type | Règle | Commentaire | Exemple |
|---|---|---|---|---|
| document_composant_id | TEXT | PK; FK → document_composant.id |  | DC-08-A-275-0001 |
| gamme | TEXT | NOT NULL | 'PYROSWISS', 'PYROSTOP', 'CONTRAFLAM STRUCTURE' | CONTRAFLAM LITE |
| designation | TEXT | NOT NULL | 'Pyrostop 60-101' | Pyrostop 60-101 |
| type_vitrage_code | TEXT | NOT NULL; FK → ref_type_vitrage.code |  | isolant |
| epaisseur_mm | REAL |  |  | 5.0 |
| epaisseur_min_mm | REAL |  |  | 38.0 |
| epaisseur_max_mm | REAL |  |  | 54.0 |
| classe_nominale | TEXT |  | tel qu'affiché dans le nom commercial ('E30', 'EW30', '60') | 60 |
| intercalaire_min_mm | REAL |  |  | 8.0 |
| intercalaire_max_mm | REAL |  |  | 16.0 |
| composition_detaillee_disponible | INTEGER | CHECK composition_detaillee_disponible IN (0,1) | 0 = « en possession du laboratoire » | 0 |

## `dimension` (327 lignes)

| Colonne | Type | Règle | Commentaire | Exemple |
|---|---|---|---|---|
| id | TEXT | PK |  | FMT-08-A-275-0001-hauteur-autorise_max |
| format_id | TEXT | NOT NULL; FK → dimension_format.id |  | FMT-08-A-275-0001 |
| grandeur_code | TEXT | NOT NULL; FK → ref_grandeur.code |  | angle |
| nature_code | TEXT | NOT NULL; FK → ref_nature_valeur.code |  | autorise_max |
| operateur_code | TEXT | NOT NULL; FK → ref_operateur.code |  | le |
| valeur_origine | TEXT | NOT NULL | tel qu'écrit : '1610', 'sans limite', '4,54 m²' | 4000 |
| unite_origine | TEXT |  | tel qu'écrit : 'mm', 'm²' | mm |
| valeur_norm | REAL |  | NULL si sans limite | 180.0 |
| unite_norm_code | TEXT | FK → ref_unite.code |  | mm |
| sans_limite | INTEGER | NOT NULL; défaut 0; CHECK sans_limite IN (0,1) |  | 0 |
| tolerance_plus | REAL |  |  | 3.0 |
| tolerance_moins | REAL |  |  | 5.0 |
| statut_extraction | TEXT | NOT NULL; FK → ref_statut_extraction.code; défaut 'extrait' |  | extrait |

## `dimension_format` (174 lignes)

| Colonne | Type | Règle | Commentaire | Exemple |
|---|---|---|---|---|
| id | TEXT | PK |  | FMT-08-A-275-0001 |
| document_id | TEXT | NOT NULL; FK → document.id |  | DOC-08-A-275 |
| configuration_id | TEXT | FK → configuration.id |  | CFG-08-A-275-CV |
| document_composant_id | TEXT | FK → document_composant.id | ex. vitrage concerné | DC-08-A-275-0001 |
| objet_code | TEXT | NOT NULL; FK → ref_objet_dimension.code |  | allege |
| libelle | TEXT | NOT NULL |  | Cloison — support forte densité (1600 à 2200 kg/m³) |
| groupe_alternative | TEXT |  | même valeur = formats alternatifs (« OU ») | P101 |
| orientation | TEXT | CHECK orientation IS NULL OR orientation IN ('portrait','paysage','indifferent') |  | paysage |
| source_page_id | TEXT | FK → source_page.id |  | SP-08-A-275-P008-4-3-1 |
| statut_extraction | TEXT | NOT NULL; FK → ref_statut_extraction.code; défaut 'extrait' |  | extrait |

## `document` (38 lignes)

| Colonne | Type | Règle | Commentaire | Exemple |
|---|---|---|---|---|
| id | TEXT | PK | 'DOC-<numero_normalise>[-R<rev>]' | DOC-08-A-275 |
| numero | TEXT | NOT NULL | tel qu'écrit : '11 - A - 507', '22/2' | 08 - A - 275 |
| numero_normalise | TEXT | NOT NULL | '11-A-507', '11-A-507/EXT-22/2' | 08-A-275 |
| revision | TEXT |  | '1', NULL si aucune | 0 |
| type_code | TEXT | NOT NULL; FK → ref_type_document.code |  | appreciation_laboratoire |
| domaine_code | TEXT | NOT NULL; FK → ref_domaine_performance.code; défaut 'feu' |  | feu |
| objet | TEXT |  | intitulé « Concernant » (court) | Cloison vitrée à ossature métallique thermiquement isolée — Fuego Ligh |
| laboratoire_id | TEXT | FK → organisme.id |  | ORG-EFECTIS-FRANCE |
| date_emission | TEXT | CHECK date_emission IS NULL OR date_emission GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]' |  | 2009-02-16 |
| date_validite | TEXT | CHECK date_validite IS NULL OR date_validite GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]' |  | 2014-02-16 |
| validite_liee_au_pv | INTEGER | NOT NULL; défaut 0; CHECK validite_liee_au_pv IN (0,1) | extensions : validité = celle du PV | 0 |
| nb_pages | INTEGER | CHECK nb_pages IS NULL OR nb_pages > 0 |  | 35 |
| arrete_reference | TEXT |  |  | Arrêté du 22 mars 2004 |
| numeros_affaire | TEXT |  | liste séparée par ';' | EFR-20-001690 |
| fichier_source_id | TEXT | FK → fichier_source.id |  | FIC-08-A-275 |
| ordre_dans_fichier | INTEGER |  |  | 3 |
| present_dans_corpus | INTEGER | NOT NULL; défaut 1; CHECK present_dans_corpus IN (0,1) | 0 = cité mais non fourni | 1 |
| statut_extraction | TEXT | NOT NULL; FK → ref_statut_extraction.code; défaut 'extrait' |  | extrait |
| commentaire | TEXT |  |  | Reconduite par 19/2, explicitement non reconduite par 24/3 ; non fourn |

## `document_composant` (630 lignes)

| Colonne | Type | Règle | Commentaire | Exemple |
|---|---|---|---|---|
| id | TEXT | PK |  | DC-08-A-275-0001 |
| document_id | TEXT | NOT NULL; FK → document.id |  | DOC-08-A-275 |
| configuration_id | TEXT | FK → configuration.id |  | CFG-08-A-275-CV |
| reference_id | TEXT | FK → reference_composant.id | NULL si composant sans référence (« serrure à mortaiser 1 point ») | REF-3M-FASARA20PL |
| reference_brute | TEXT |  | exactement comme écrit ; NULL si non référencé | 01.535 |
| designation_document | TEXT | NOT NULL | libellé dans le document | Pyrostop 60-101 |
| categorie_code | TEXT | NOT NULL; FK → ref_categorie_composant.code |  | accessoire |
| role_code | TEXT | NOT NULL; FK → ref_role_composant.code |  | maintien_remplissage |
| localisation_code | TEXT | FK → ref_localisation.code |  | cloison |
| statut_autorisation_code | TEXT | NOT NULL; FK → ref_statut_autorisation.code; défaut 'autorise' |  | autorise |
| quantite_min | INTEGER |  |  |  |
| condition_texte | TEXT |  | condition d'emploi, telle qu'énoncée | Qualité intérieure (pl. 25) |
| parent_id | TEXT | FK → document_composant.id | composition (kit -> coffre, gâche) | DC-11-A-507-0111 |
| role_dans_parent | TEXT |  |  | coffre |
| source_page_id | TEXT | FK → source_page.id |  | SP-08-A-275-P004-1-2-2 |
| statut_extraction | TEXT | NOT NULL; FK → ref_statut_extraction.code; défaut 'extrait' |  | extrait |

## `document_essai` (11 lignes)

| Colonne | Type | Règle | Commentaire | Exemple |
|---|---|---|---|---|
| document_id | TEXT | NOT NULL; FK → document.id |  | DOC-08-A-275-EXT-20-2 |
| essai_id | TEXT | NOT NULL; FK → essai.id |  | ESS-01-V-234 |
| role | TEXT | NOT NULL; CHECK role IN ('justification','reference','complement') |  | justification |
| source_page_id | TEXT | FK → source_page.id |  | SP-08-A-275-REC-19-2-P002-ANALYSE |

## `document_norme` (23 lignes)

| Colonne | Type | Règle | Commentaire | Exemple |
|---|---|---|---|---|
| document_id | TEXT | NOT NULL; FK → document.id |  | DOC-08-A-275 |
| norme_id | TEXT | NOT NULL; FK → norme.id |  | NRM-ARRETE-DU-14-MARS-2011-2011 |
| role | TEXT | NOT NULL; CHECK role IN ('classement','essai','exclusion','reference') |  | classement |
| paragraphe | TEXT |  |  | §7.5.2 |
| source_page_id | TEXT | FK → source_page.id |  | SP-08-A-275-P007-3-1 |

## `document_organisme` (61 lignes)

| Colonne | Type | Règle | Commentaire | Exemple |
|---|---|---|---|---|
| document_id | TEXT | NOT NULL; FK → document.id |  | DOC-08-A-275 |
| organisme_id | TEXT | NOT NULL; FK → organisme.id |  | ORG-EFECTIS-FRANCE |
| role_code | TEXT | NOT NULL; FK → ref_role_organisme.code |  | laboratoire |
| nom_tel_qu_ecrit | TEXT |  |  | FORSTER ROHR PROFILTECHNIK AG / FORSTER SYSTEMES DE PROFILES |
| source_page_id | TEXT | FK → source_page.id |  | SP-08-A-275-P001 |

## `document_relation` (45 lignes)

| Colonne | Type | Règle | Commentaire | Exemple |
|---|---|---|---|---|
| id | TEXT | PK |  | REL-08-A-275-EXT-18-1-etend-08-A-275 |
| document_source_id | TEXT | NOT NULL; FK → document.id |  | DOC-08-A-275 |
| document_cible_id | TEXT | NOT NULL; FK → document.id |  | DOC-08-A-275 |
| type_relation_code | TEXT | NOT NULL; FK → ref_type_relation.code |  | etend |
| date_relation | TEXT |  |  | 2024-06-03 |
| commentaire | TEXT |  |  | « L'extension 18/1 n'est pas reconduite » |
| source_page_id | TEXT | FK → source_page.id |  | SP-08-A-275-REC-24-3-P001-DUREE-DE-VALIDITE |

## `document_signataire` (34 lignes)

| Colonne | Type | Règle | Commentaire | Exemple |
|---|---|---|---|---|
| document_id | TEXT | NOT NULL; FK → document.id |  | DOC-08-A-275 |
| intervenant_id | TEXT | NOT NULL; FK → intervenant.id |  | PER-HERVE-RYCKEWAERT |
| fonction | TEXT |  |  | Ingénieur chargé d'affaires |

## `document_systeme` (11 lignes)

| Colonne | Type | Règle | Commentaire | Exemple |
|---|---|---|---|---|
| document_id | TEXT | NOT NULL; FK → document.id |  | DOC-08-A-275 |
| systeme_id | TEXT | NOT NULL; FK → systeme.id |  | SYS-FUEGO-LIGHT-30 |
| role | TEXT | NOT NULL; CHECK role IN ('principal','variante','support_associe','integration') |  | principal |
| source_page_id | TEXT | FK → source_page.id |  | SP-08-A-275-P001 |

## `enrichissement_externe` (12 lignes)

| Colonne | Type | Règle | Commentaire | Exemple |
|---|---|---|---|---|
| id | TEXT | PK |  | ENR-0001 |
| reference_id | TEXT | NOT NULL; FK → reference_composant.id |  | REF-DORMA-HZ43F |
| type_caracteristique_code | TEXT | NOT NULL; FK → ref_type_caracteristique.code |  | fonction |
| valeur_texte | TEXT |  |  | Ferme-porte à glissière (technologie à came) |
| valeur_num | REAL |  |  | 1400.0 |
| valeur_bool | INTEGER | CHECK valeur_bool IS NULL OR valeur_bool IN (0,1) |  | 1 |
| unite_code | TEXT | FK → ref_unite.code |  | mm |
| source | TEXT | NOT NULL; défaut 'enrichissement'; CHECK source = 'enrichissement' |  | enrichissement |
| source_libelle | TEXT | NOT NULL |  | dormakaba — brochure technique TS 93 (FR) |
| source_url | TEXT |  |  | https://dormakaba.rokka.io/original/324fdc/120000010769_dormakaba-ferm |
| date_recherche | TEXT | NOT NULL |  | 2026-11-10 |
| statut_fiabilite_code | TEXT | NOT NULL; FK → ref_statut_fiabilite.code |  | a_verifier |
| commentaire | TEXT |  |  | Deux tailles de corps ; le PV ne précise pas la taille |

## `essai` (10 lignes)

| Colonne | Type | Règle | Commentaire | Exemple |
|---|---|---|---|---|
| id | TEXT | PK |  | ESS-01-V-234 |
| reference | TEXT | NOT NULL; UNIQUE | 'EFR-21-002096-B', '08-G-053' | 01-V-234 |
| laboratoire_id | TEXT | FK → organisme.id |  | ORG-DMT |
| norme_id | TEXT | FK → norme.id |  | NRM-EN-1634-1-2008 |
| date_essai | TEXT |  |  | 2011-11-23 |
| objet | TEXT |  |  | Bloc-porte à deux vantaux tôlés sur bâti acier muni d'un verrou HZ43F  |
| systeme_teste | TEXT |  | tel qu'écrit (peut être hors gamme Forster) | Presto 50 |

## `essai_resultat` (15 lignes)

| Colonne | Type | Règle | Commentaire | Exemple |
|---|---|---|---|---|
| id | TEXT | PK |  | ESS-01-V-234-RES-E-015 |
| essai_id | TEXT | NOT NULL; FK → essai.id |  | ESS-01-V-234 |
| critere_code | TEXT | NOT NULL; FK → ref_critere_feu.code |  | E |
| duree_min | REAL | NOT NULL; CHECK duree_min >= 0 |  | 60.0 |
| operateur_code | TEXT | NOT NULL; FK → ref_operateur.code; défaut 'eq' | 'gt' = « plus de » | gt |
| condition_essai | TEXT |  | sens du feu, éprouvette | Sens du feu côté opposé aux paumelles |
| nature_code | TEXT | NOT NULL; FK → ref_nature_valeur.code; défaut 'teste'; CHECK nature_code = 'teste') REFERENCES ref_nature_valeur(code |  | teste |
| source_page_id | TEXT | FK → source_page.id |  | SP-EFR-14-000468-P002-1-4 |

## `fichier_source` (6 lignes)

| Colonne | Type | Règle | Commentaire | Exemple |
|---|---|---|---|---|
| id | TEXT | PK |  | FIC-08-A-275 |
| nom_fichier | TEXT | NOT NULL; UNIQUE |  | FR 08-A-275 - PILK - cloison FUEGO light EI60 - COPRO - 16-02-2029.pdf |
| drive_file_id | TEXT | UNIQUE |  | 1BHDHbWzNLF_1nROu6-614WGvZBHTUydn |
| url | TEXT |  |  | https://drive.google.com/file/d/1wLRTFiFA9yKb7fNvpt4yLitiBmBKxH1-/view |
| taille_octets | INTEGER | CHECK taille_octets IS NULL OR taille_octets > 0 |  | 12720683 |
| date_modification | TEXT |  | ISO 8601 | 2024-06-10 |
| code_fournisseur_vitrage | TEXT |  | segment du nom de fichier (VETR, PYRO, PILK, POLF) | PILK |
| code_marche | TEXT |  | segment du nom de fichier (COPRO, PROFOR) | COPRO |
| commentaire | TEXT |  |  | Compilation : reconduction 24/3, reconduction 19/2, PV 08-A-275, exten |

## `intervenant` (10 lignes)

| Colonne | Type | Règle | Commentaire | Exemple |
|---|---|---|---|---|
| id | TEXT | PK |  | PER-ANDREA-VIARD |
| nom | TEXT | NOT NULL; UNIQUE |  | Andréa VIARD |

## `meta_schema` (4 lignes)

| Colonne | Type | Règle | Commentaire | Exemple |
|---|---|---|---|---|
| cle | TEXT | PK |  | data_sha256 |
| valeur | TEXT | NOT NULL |  | 1.0.0 |

## `norme` (20 lignes)

| Colonne | Type | Règle | Commentaire | Exemple |
|---|---|---|---|---|
| id | TEXT | PK |  | NRM-ARRETE-DU-14-MARS-2011-2011 |
| code | TEXT | NOT NULL | 'EN 13501-2' | Arrêté du 14 mars 2011 |
| annee | TEXT |  | '2016', '2004' | 2011 |
| amendement | TEXT |  | '+A1:2018' | +A1:2018 |
| titre | TEXT |  |  | Résistance au feu des produits, éléments de construction et d'ouvrages |

## `organisme` (38 lignes)

| Colonne | Type | Règle | Commentaire | Exemple |
|---|---|---|---|---|
| id | TEXT | PK |  | ORG-3M |
| nom | TEXT | NOT NULL | tel qu'écrit (première occurrence) | Efectis France |
| nom_normalise | TEXT | NOT NULL; UNIQUE | MAJUSCULES sans accents | 3M |
| pays_code | TEXT |  | ISO 3166-1 alpha-2 | FR |
| ville | TEXT |  |  | Maizières-lès-Metz |
| adresse | TEXT |  |  | Voie Romaine F-57280 Maizières-lès-Metz |
| est_fabricant | INTEGER | NOT NULL; défaut 0; CHECK est_fabricant IN (0,1) |  | 0 |
| est_laboratoire | INTEGER | NOT NULL; défaut 0; CHECK est_laboratoire IN (0,1) |  | 1 |

## `organisme_alias` (11 lignes)

| Colonne | Type | Règle | Commentaire | Exemple |
|---|---|---|---|---|
| organisme_id | TEXT | NOT NULL; FK → organisme.id |  | ORG-EFECTIS-FRANCE |
| alias | TEXT | NOT NULL |  | EFECTIS France Espace Technologique Saint-Aubin |

## `perf_acoustique` (0 lignes)

| Colonne | Type | Règle | Commentaire | Exemple |
|---|---|---|---|---|
| performance_id | TEXT | PK; FK → performance.id |  |  |
| rw_db | REAL | NOT NULL |  |  |
| c_db | REAL |  |  |  |
| ctr_db | REAL |  |  |  |
| norme_id | TEXT | FK → norme.id |  |  |

## `perf_aev` (0 lignes)

| Colonne | Type | Règle | Commentaire | Exemple |
|---|---|---|---|---|
| performance_id | TEXT | PK; FK → performance.id |  |  |
| classe_air | TEXT |  | '4' |  |
| classe_eau | TEXT |  | '9A', 'E1050' |  |
| classe_vent | TEXT |  | 'C3' |  |
| pression_air_pa | REAL |  |  |  |
| pression_eau_pa | REAL |  |  |  |
| pression_vent_pa | REAL |  |  |  |
| norme_id | TEXT | FK → norme.id |  |  |

## `perf_balistique` (0 lignes)

| Colonne | Type | Règle | Commentaire | Exemple |
|---|---|---|---|---|
| performance_id | TEXT | PK; FK → performance.id |  |  |
| classe | TEXT | NOT NULL | 'FB4', 'BR4' |  |
| avec_eclats | TEXT | CHECK avec_eclats IS NULL OR avec_eclats IN ('S','NS') |  |  |
| arme_munition | TEXT |  |  |  |
| norme_id | TEXT | FK → norme.id |  |  |

## `perf_effraction` (0 lignes)

| Colonne | Type | Règle | Commentaire | Exemple |
|---|---|---|---|---|
| performance_id | TEXT | PK; FK → performance.id |  |  |
| classe_rc | TEXT | NOT NULL; CHECK classe_rc IN ('RC1','RC1N','RC2','RC2N','RC3','RC4','RC5','RC6') |  |  |
| norme_id | TEXT | FK → norme.id |  |  |
| duree_resistance_min | REAL |  |  |  |

## `perf_feu` (17 lignes)

| Colonne | Type | Règle | Commentaire | Exemple |
|---|---|---|---|---|
| performance_id | TEXT | PK; FK → performance.id |  | PRF-08-A-275-0001 |
| critere_r | INTEGER | NOT NULL; défaut 0; CHECK critere_r IN (0,1) |  | 0 |
| critere_e | INTEGER | NOT NULL; défaut 0; CHECK critere_e IN (0,1) |  | 1 |
| critere_i | INTEGER | NOT NULL; défaut 0; CHECK critere_i IN (0,1) |  | 0 |
| variante_i | TEXT | CHECK variante_i IS NULL OR variante_i IN ('I','I1','I2') |  | I |
| critere_w | INTEGER | NOT NULL; défaut 0; CHECK critere_w IN (0,1) |  | 0 |
| critere_m | INTEGER | NOT NULL; défaut 0; CHECK critere_m IN (0,1) |  | 0 |
| critere_c | INTEGER | NOT NULL; défaut 0; CHECK critere_c IN (0,1) |  | 0 |
| classe_c | TEXT |  | C0..C5 si applicable |  |
| critere_s | INTEGER | NOT NULL; défaut 0; CHECK critere_s IN (0,1) |  | 0 |
| duree_min | INTEGER | NOT NULL; CHECK duree_min IN (15,20,30,45,60,90,120,180,240) |  | 30 |
| sens_feu | TEXT |  | résumé ; le détail est dans restriction(type 'sens_feu') | Indifférent |

## `performance` (17 lignes)

| Colonne | Type | Règle | Commentaire | Exemple |
|---|---|---|---|---|
| id | TEXT | PK |  | PRF-08-A-275-0001 |
| document_id | TEXT | NOT NULL; FK → document.id |  | DOC-08-A-275 |
| configuration_id | TEXT | FK → configuration.id |  | CFG-08-A-275-CV |
| domaine_code | TEXT | NOT NULL; FK → ref_domaine_performance.code |  | feu |
| libelle_tel_qu_ecrit | TEXT | NOT NULL | 'E I2 30' | EI 60 |
| classe_normalisee | TEXT | NOT NULL | 'EI2 30' | E 30 |
| nature_code | TEXT | NOT NULL; FK → ref_nature_valeur.code; défaut 'classement' |  | classement |
| condition_texte | TEXT |  |  | Avec vitrages CONTRAFLAM LITE 30 MONOLITHIQUE ou CLIMAPLUS/CLIMALIT |
| source_page_id | TEXT | FK → source_page.id |  | SP-08-A-275-P007-3-2 |
| statut_extraction | TEXT | NOT NULL; FK → ref_statut_extraction.code; défaut 'extrait' |  | extrait |

## `recherche_index` (749 lignes)

| Colonne | Type | Règle | Commentaire | Exemple |
|---|---|---|---|---|
| objet_type | TEXT | NOT NULL |  | configuration |
| objet_id | TEXT | NOT NULL |  | CFG-08-A-275-CV |
| document_id | TEXT | FK → document.id |  | DOC-08-A-275 |
| texte | TEXT | NOT NULL | minuscules, sans accents | 08 - a - 275 08-a-275 cloison vitree a ossature metallique thermiqueme |

## `reference_alias` (6 lignes)

| Colonne | Type | Règle | Commentaire | Exemple |
|---|---|---|---|---|
| reference_id | TEXT | NOT NULL; FK → reference_composant.id |  | REF-DORMA-HZ43F |
| alias | TEXT | NOT NULL |  | 209XKAB |
| type_alias | TEXT | NOT NULL; CHECK type_alias IN ('ecriture_document','ancienne_reference','reference_remplacee') |  | ancienne_reference |
| document_id | TEXT | FK → document.id |  | DOC-11-A-507 |

## `reference_composant` (359 lignes)

| Colonne | Type | Règle | Commentaire | Exemple |
|---|---|---|---|---|
| id | TEXT | PK | 'REF-FORSTER-907720' | REF-3M-FASARA20PL |
| reference_normalisee | TEXT | NOT NULL | sans espaces/points superflus, majuscules | 01535 |
| fabricant_id | TEXT | FK → organisme.id |  | ORG-3M |
| categorie_code | TEXT | NOT NULL; FK → ref_categorie_composant.code |  | bande_fibre |
| designation | TEXT |  | désignation générique issue des documents | Montant et traverse d'huisserie |

## `restriction` (63 lignes)

| Colonne | Type | Règle | Commentaire | Exemple |
|---|---|---|---|---|
| id | TEXT | PK |  | RST-08-A-275-0001 |
| document_id | TEXT | NOT NULL; FK → document.id |  | DOC-08-A-275 |
| configuration_id | TEXT | FK → configuration.id |  | CFG-08-A-275-CV |
| document_composant_id | TEXT | FK → document_composant.id |  | DC-11-A-507-0286 |
| type_code | TEXT | NOT NULL; FK → ref_type_restriction.code |  | condition_combinaison |
| libelle | TEXT | NOT NULL | résumé filtrable | Sens du feu indifférent |
| texte_source | TEXT |  | extrait court du document | Indifférent pour l'ossature |
| source_page_id | TEXT | FK → source_page.id |  | SP-08-A-275-P007-4-2 |

## `source_page` (167 lignes)

| Colonne | Type | Règle | Commentaire | Exemple |
|---|---|---|---|---|
| id | TEXT | PK |  | SP-08-A-275-EXT-20-2-P002-1-2 |
| document_id | TEXT | NOT NULL; FK → document.id |  | DOC-08-A-275 |
| page_doc | INTEGER |  | page selon la pagination du document ('Page 4/60' -> 4) | 1 |
| page_doc_total | INTEGER |  |  | 35 |
| section | TEXT |  | '§1.2.7.2', '§4.3.2' | §1 |
| planche | TEXT |  | 'Planche 30' | Planche 1 |
| type_zone_code | TEXT | NOT NULL; FK → ref_type_zone_source.code |  | page_garde |
| libelle | TEXT |  |  |  |

## `support_pose` (32 lignes)

| Colonne | Type | Règle | Commentaire | Exemple |
|---|---|---|---|---|
| id | TEXT | PK |  | SUP-08-A-275-0001 |
| document_id | TEXT | NOT NULL; FK → document.id |  | DOC-08-A-275 |
| configuration_id | TEXT | FK → configuration.id |  | CFG-08-A-275-CV |
| type_support_code | TEXT | NOT NULL; FK → ref_type_support.code |  | beton_arme |
| masse_vol_min_kg_m3 | REAL |  |  | 2200.0 |
| masse_vol_operateur_code | TEXT | FK → ref_operateur.code |  | gt |
| epaisseur_min_mm | REAL |  |  | 150.0 |
| epaisseur_operateur_code | TEXT | FK → ref_operateur.code |  | gt |
| classement_pv_exige | TEXT |  | ex. 'EI 60' | EI 60 |
| prolongation_laterale | INTEGER | CHECK prolongation_laterale IN (0,1) |  | 1 |
| imposte_autorisee | INTEGER | CHECK imposte_autorisee IN (0,1) |  | 1 |
| allege_autorisee | INTEGER | CHECK allege_autorisee IN (0,1) |  | 0 |
| pas_fixation_max_mm | REAL |  |  | 650.0 |
| condition_texte | TEXT |  |  | Vis HUS Ø7,5x160 et chevilles nylon après cales Promatect H |
| source_page_id | TEXT | FK → source_page.id |  | SP-08-A-275-P005-1-2-5-1 |

## `systeme` (5 lignes)

| Colonne | Type | Règle | Commentaire | Exemple |
|---|---|---|---|---|
| id | TEXT | PK | 'SYS-PRESTO-50' | SYS-FUEGO-LIGHT-30 |
| nom | TEXT | NOT NULL | 'Presto 50' | Presto 50 |
| nom_normalise | TEXT | NOT NULL; UNIQUE | 'PRESTO 50' | FUEGO LIGHT 30 |
| fabricant_id | TEXT | NOT NULL; FK → organisme.id |  | ORG-FORSTER |
| isolation_thermique | INTEGER | CHECK isolation_thermique IN (0,1) |  | 0 |
| profondeur_mm | REAL |  |  | 50.0 |
| commentaire | TEXT |  |  | Profils acier non isolés, profondeur 50 mm |
