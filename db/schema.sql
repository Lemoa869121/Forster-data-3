-- =====================================================================
-- Base PV Forster — schéma SQLite (compatible sql.js / SQLite >= 3.31)
-- Version de schéma : voir table meta_schema (clé 'schema_version')
-- Conventions :
--   * Clés primaires TEXT stables et lisibles (ex. 'DOC-11-A-507') :
--     import idempotent, diffs Git lisibles, pas de renumérotation.
--   * Toute donnée issue d'un document porte source_page_id.
--   * Toute donnée externe vit dans enrichissement_externe (jamais ailleurs).
--   * Valeur testée / valeur autorisée : colonne nature_code obligatoire.
--   * Absence d'information : NULL + statut_extraction = 'non_trouve'
--     (jamais de chaîne vide : CHECK (col <> '')).
-- =====================================================================
PRAGMA foreign_keys = ON;

-- ---------------------------------------------------------------------
-- 0. Méta
-- ---------------------------------------------------------------------
CREATE TABLE meta_schema (
  cle    TEXT PRIMARY KEY,
  valeur TEXT NOT NULL
);

-- ---------------------------------------------------------------------
-- 1. Référentiels contrôlés (listes de valeurs)
--    Toutes de forme (code PK, libelle, description).
-- ---------------------------------------------------------------------
CREATE TABLE ref_type_document      (code TEXT PRIMARY KEY, libelle TEXT NOT NULL, description TEXT);
CREATE TABLE ref_type_relation      (code TEXT PRIMARY KEY, libelle TEXT NOT NULL, description TEXT);
CREATE TABLE ref_role_organisme     (code TEXT PRIMARY KEY, libelle TEXT NOT NULL, description TEXT);
CREATE TABLE ref_domaine_performance(code TEXT PRIMARY KEY, libelle TEXT NOT NULL, description TEXT);
CREATE TABLE ref_typologie          (code TEXT PRIMARY KEY, libelle TEXT NOT NULL, description TEXT);
CREATE TABLE ref_categorie_composant(code TEXT PRIMARY KEY, libelle TEXT NOT NULL, famille TEXT NOT NULL, description TEXT);
CREATE TABLE ref_role_composant     (code TEXT PRIMARY KEY, libelle TEXT NOT NULL, description TEXT);
CREATE TABLE ref_localisation       (code TEXT PRIMARY KEY, libelle TEXT NOT NULL, description TEXT);
CREATE TABLE ref_statut_autorisation(code TEXT PRIMARY KEY, libelle TEXT NOT NULL, description TEXT);
CREATE TABLE ref_type_caracteristique(
  code TEXT PRIMARY KEY, libelle TEXT NOT NULL,
  type_valeur TEXT NOT NULL CHECK (type_valeur IN ('texte','entier','reel','booleen')),
  unite_code TEXT REFERENCES ref_unite(code), description TEXT);
CREATE TABLE ref_nature_valeur      (code TEXT PRIMARY KEY, libelle TEXT NOT NULL, description TEXT);
CREATE TABLE ref_objet_dimension    (code TEXT PRIMARY KEY, libelle TEXT NOT NULL, description TEXT);
CREATE TABLE ref_grandeur           (code TEXT PRIMARY KEY, libelle TEXT NOT NULL, unite_code TEXT REFERENCES ref_unite(code));
CREATE TABLE ref_unite              (code TEXT PRIMARY KEY, libelle TEXT NOT NULL, facteur_vers_si REAL);
CREATE TABLE ref_statut_fiabilite   (code TEXT PRIMARY KEY, libelle TEXT NOT NULL, description TEXT);
CREATE TABLE ref_statut_extraction  (code TEXT PRIMARY KEY, libelle TEXT NOT NULL, description TEXT);
CREATE TABLE ref_type_restriction   (code TEXT PRIMARY KEY, libelle TEXT NOT NULL, description TEXT);
CREATE TABLE ref_type_support       (code TEXT PRIMARY KEY, libelle TEXT NOT NULL, famille TEXT NOT NULL, description TEXT);
CREATE TABLE ref_fonction_serrure   (code TEXT PRIMARY KEY, libelle TEXT NOT NULL, description TEXT);
CREATE TABLE ref_type_serrure       (code TEXT PRIMARY KEY, libelle TEXT NOT NULL, description TEXT);
CREATE TABLE ref_type_zone_source   (code TEXT PRIMARY KEY, libelle TEXT NOT NULL, description TEXT);
CREATE TABLE ref_type_controle      (code TEXT PRIMARY KEY, libelle TEXT NOT NULL, description TEXT);
CREATE TABLE ref_critere_feu        (code TEXT PRIMARY KEY, libelle TEXT NOT NULL, description TEXT);
CREATE TABLE ref_type_joint         (code TEXT PRIMARY KEY, libelle TEXT NOT NULL, description TEXT);
CREATE TABLE ref_type_vitrage       (code TEXT PRIMARY KEY, libelle TEXT NOT NULL, description TEXT);
CREATE TABLE ref_type_articulation  (code TEXT PRIMARY KEY, libelle TEXT NOT NULL, description TEXT);
CREATE TABLE ref_type_ferme_porte   (code TEXT PRIMARY KEY, libelle TEXT NOT NULL, description TEXT);
CREATE TABLE ref_type_fixation      (code TEXT PRIMARY KEY, libelle TEXT NOT NULL, description TEXT);
CREATE TABLE ref_operateur          (code TEXT PRIMARY KEY, libelle TEXT NOT NULL);

-- ---------------------------------------------------------------------
-- 2. Sources et documents
-- ---------------------------------------------------------------------
-- Fichier physique (un PDF peut compiler plusieurs documents logiques :
-- reconduction + PV + extensions).
CREATE TABLE fichier_source (
  id              TEXT PRIMARY KEY,
  nom_fichier     TEXT NOT NULL UNIQUE,
  drive_file_id   TEXT UNIQUE,
  url             TEXT,
  taille_octets   INTEGER CHECK (taille_octets IS NULL OR taille_octets > 0),
  date_modification TEXT,               -- ISO 8601
  code_fournisseur_vitrage TEXT,        -- segment du nom de fichier (VETR, PYRO, PILK, POLF)
  code_marche     TEXT,                 -- segment du nom de fichier (COPRO, PROFOR)
  commentaire     TEXT,
  CHECK (nom_fichier <> '')
);

CREATE TABLE document (
  id                   TEXT PRIMARY KEY,           -- 'DOC-<numero_normalise>[-R<rev>]'
  numero               TEXT NOT NULL,              -- tel qu'écrit : '11 - A - 507', '22/2'
  numero_normalise     TEXT NOT NULL,              -- '11-A-507', '11-A-507/EXT-22/2'
  revision             TEXT,                       -- '1', NULL si aucune
  type_code            TEXT NOT NULL REFERENCES ref_type_document(code),
  domaine_code         TEXT NOT NULL DEFAULT 'feu' REFERENCES ref_domaine_performance(code),
  objet                TEXT,                       -- intitulé « Concernant » (court)
  laboratoire_id       TEXT REFERENCES organisme(id),
  date_emission        TEXT CHECK (date_emission IS NULL OR date_emission GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'),
  date_validite        TEXT CHECK (date_validite IS NULL OR date_validite GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'),
  validite_liee_au_pv  INTEGER NOT NULL DEFAULT 0 CHECK (validite_liee_au_pv IN (0,1)), -- extensions : validité = celle du PV
  nb_pages             INTEGER CHECK (nb_pages IS NULL OR nb_pages > 0),
  arrete_reference     TEXT,
  numeros_affaire      TEXT,                       -- liste séparée par ';'
  fichier_source_id    TEXT REFERENCES fichier_source(id),
  ordre_dans_fichier   INTEGER,
  present_dans_corpus  INTEGER NOT NULL DEFAULT 1 CHECK (present_dans_corpus IN (0,1)), -- 0 = cité mais non fourni
  statut_extraction    TEXT NOT NULL DEFAULT 'extrait' REFERENCES ref_statut_extraction(code),
  commentaire          TEXT,
  UNIQUE (numero_normalise, revision),
  CHECK (numero <> '' AND numero_normalise <> '')
);

CREATE TABLE source_page (
  id             TEXT PRIMARY KEY,
  document_id    TEXT NOT NULL REFERENCES document(id) ON DELETE CASCADE,
  page_doc       INTEGER,            -- page selon la pagination du document ('Page 4/60' -> 4)
  page_doc_total INTEGER,
  section        TEXT,               -- '§1.2.7.2', '§4.3.2'
  planche        TEXT,               -- 'Planche 30'
  type_zone_code TEXT NOT NULL REFERENCES ref_type_zone_source(code),
  libelle        TEXT,
  UNIQUE (document_id, page_doc, section, planche)
);

CREATE TABLE document_relation (
  id                  TEXT PRIMARY KEY,
  document_source_id  TEXT NOT NULL REFERENCES document(id) ON DELETE CASCADE,
  document_cible_id   TEXT NOT NULL REFERENCES document(id) ON DELETE CASCADE,
  type_relation_code  TEXT NOT NULL REFERENCES ref_type_relation(code),
  date_relation       TEXT,
  commentaire         TEXT,
  source_page_id      TEXT REFERENCES source_page(id),
  UNIQUE (document_source_id, document_cible_id, type_relation_code),
  CHECK (document_source_id <> document_cible_id)
);

-- ---------------------------------------------------------------------
-- 3. Organismes, intervenants, normes, essais
-- ---------------------------------------------------------------------
CREATE TABLE organisme (
  id             TEXT PRIMARY KEY,
  nom            TEXT NOT NULL,            -- tel qu'écrit (première occurrence)
  nom_normalise  TEXT NOT NULL UNIQUE,     -- MAJUSCULES sans accents
  pays_code      TEXT,                     -- ISO 3166-1 alpha-2
  ville          TEXT,
  adresse        TEXT,
  est_fabricant  INTEGER NOT NULL DEFAULT 0 CHECK (est_fabricant IN (0,1)),
  est_laboratoire INTEGER NOT NULL DEFAULT 0 CHECK (est_laboratoire IN (0,1))
);

CREATE TABLE organisme_alias (
  organisme_id TEXT NOT NULL REFERENCES organisme(id) ON DELETE CASCADE,
  alias        TEXT NOT NULL,
  PRIMARY KEY (organisme_id, alias)
);

CREATE TABLE document_organisme (
  document_id   TEXT NOT NULL REFERENCES document(id) ON DELETE CASCADE,
  organisme_id  TEXT NOT NULL REFERENCES organisme(id),
  role_code     TEXT NOT NULL REFERENCES ref_role_organisme(code),
  nom_tel_qu_ecrit TEXT,
  source_page_id TEXT REFERENCES source_page(id),
  PRIMARY KEY (document_id, organisme_id, role_code)
);

CREATE TABLE intervenant (
  id   TEXT PRIMARY KEY,
  nom  TEXT NOT NULL UNIQUE
);

CREATE TABLE document_signataire (
  document_id    TEXT NOT NULL REFERENCES document(id) ON DELETE CASCADE,
  intervenant_id TEXT NOT NULL REFERENCES intervenant(id),
  fonction       TEXT,
  PRIMARY KEY (document_id, intervenant_id)
);

CREATE TABLE norme (
  id      TEXT PRIMARY KEY,
  code    TEXT NOT NULL,          -- 'EN 13501-2'
  annee   TEXT,                   -- '2016', '2004'
  amendement TEXT,                -- '+A1:2018'
  titre   TEXT,
  UNIQUE (code, annee, amendement)
);

CREATE TABLE document_norme (
  document_id TEXT NOT NULL REFERENCES document(id) ON DELETE CASCADE,
  norme_id    TEXT NOT NULL REFERENCES norme(id),
  role        TEXT NOT NULL CHECK (role IN ('classement','essai','exclusion','reference')),
  paragraphe  TEXT,
  source_page_id TEXT REFERENCES source_page(id),
  PRIMARY KEY (document_id, norme_id, role)
);

-- Essais cités (rapports d'essai non fournis mais référencés)
CREATE TABLE essai (
  id              TEXT PRIMARY KEY,
  reference       TEXT NOT NULL UNIQUE,   -- 'EFR-21-002096-B', '08-G-053'
  laboratoire_id  TEXT REFERENCES organisme(id),
  norme_id        TEXT REFERENCES norme(id),
  date_essai      TEXT,
  objet           TEXT,
  systeme_teste   TEXT                    -- tel qu'écrit (peut être hors gamme Forster)
);

CREATE TABLE document_essai (
  document_id    TEXT NOT NULL REFERENCES document(id) ON DELETE CASCADE,
  essai_id       TEXT NOT NULL REFERENCES essai(id),
  role           TEXT NOT NULL CHECK (role IN ('justification','reference','complement')),
  source_page_id TEXT REFERENCES source_page(id),
  PRIMARY KEY (document_id, essai_id)
);

-- Résultats d'essai = VALEURS TESTÉES (durées mesurées), jamais un classement.
CREATE TABLE essai_resultat (
  id             TEXT PRIMARY KEY,
  essai_id       TEXT NOT NULL REFERENCES essai(id) ON DELETE CASCADE,
  critere_code   TEXT NOT NULL REFERENCES ref_critere_feu(code),
  duree_min      REAL NOT NULL CHECK (duree_min >= 0),
  operateur_code TEXT NOT NULL DEFAULT 'eq' REFERENCES ref_operateur(code), -- 'gt' = « plus de »
  condition_essai TEXT,                   -- sens du feu, éprouvette
  nature_code    TEXT NOT NULL DEFAULT 'teste' CHECK (nature_code = 'teste') REFERENCES ref_nature_valeur(code),
  source_page_id TEXT REFERENCES source_page(id)
);

-- ---------------------------------------------------------------------
-- 4. Produits / systèmes / configurations
-- ---------------------------------------------------------------------
CREATE TABLE systeme (
  id               TEXT PRIMARY KEY,         -- 'SYS-PRESTO-50'
  nom              TEXT NOT NULL,            -- 'Presto 50'
  nom_normalise    TEXT NOT NULL UNIQUE,     -- 'PRESTO 50'
  fabricant_id     TEXT NOT NULL REFERENCES organisme(id),
  isolation_thermique INTEGER CHECK (isolation_thermique IN (0,1)),
  profondeur_mm    REAL,
  commentaire      TEXT
);

CREATE TABLE document_systeme (
  document_id   TEXT NOT NULL REFERENCES document(id) ON DELETE CASCADE,
  systeme_id    TEXT NOT NULL REFERENCES systeme(id),
  role          TEXT NOT NULL CHECK (role IN ('principal','variante','support_associe','integration')),
  source_page_id TEXT REFERENCES source_page(id),
  PRIMARY KEY (document_id, systeme_id, role)
);

-- Une configuration = une variante technique classée (jamais fusionnée).
CREATE TABLE configuration (
  id                     TEXT PRIMARY KEY,
  document_id            TEXT NOT NULL REFERENCES document(id) ON DELETE CASCADE,
  code                   TEXT NOT NULL,          -- court, unique dans le document
  libelle                TEXT NOT NULL,
  typologie_code         TEXT NOT NULL REFERENCES ref_typologie(code),
  systeme_id             TEXT REFERENCES systeme(id),
  nb_vantaux_min         INTEGER CHECK (nb_vantaux_min IS NULL OR nb_vantaux_min BETWEEN 1 AND 2),
  nb_vantaux_max         INTEGER CHECK (nb_vantaux_max IS NULL OR nb_vantaux_max BETWEEN 1 AND 2),
  vantaux_inegaux        INTEGER CHECK (vantaux_inegaux IN (0,1)),
  vitree                 INTEGER CHECK (vitree IN (0,1)),
  parent_configuration_id TEXT REFERENCES configuration(id),
  source_page_id         TEXT REFERENCES source_page(id),
  UNIQUE (document_id, code)
);

-- ---------------------------------------------------------------------
-- 5. Performances (socle commun + tables de détail par domaine)
-- ---------------------------------------------------------------------
CREATE TABLE performance (
  id               TEXT PRIMARY KEY,
  document_id      TEXT NOT NULL REFERENCES document(id) ON DELETE CASCADE,
  configuration_id TEXT REFERENCES configuration(id) ON DELETE CASCADE,
  domaine_code     TEXT NOT NULL REFERENCES ref_domaine_performance(code),
  libelle_tel_qu_ecrit TEXT NOT NULL,     -- 'E I2 30'
  classe_normalisee TEXT NOT NULL,        -- 'EI2 30'
  nature_code      TEXT NOT NULL DEFAULT 'classement' REFERENCES ref_nature_valeur(code),
  condition_texte  TEXT,
  source_page_id   TEXT REFERENCES source_page(id),
  statut_extraction TEXT NOT NULL DEFAULT 'extrait' REFERENCES ref_statut_extraction(code)
);

-- Détail feu (EN 13501-2) : 1 ligne par performance de domaine 'feu'
CREATE TABLE perf_feu (
  performance_id TEXT PRIMARY KEY REFERENCES performance(id) ON DELETE CASCADE,
  critere_r  INTEGER NOT NULL DEFAULT 0 CHECK (critere_r IN (0,1)),
  critere_e  INTEGER NOT NULL DEFAULT 0 CHECK (critere_e IN (0,1)),
  critere_i  INTEGER NOT NULL DEFAULT 0 CHECK (critere_i IN (0,1)),
  variante_i TEXT CHECK (variante_i IS NULL OR variante_i IN ('I','I1','I2')),
  critere_w  INTEGER NOT NULL DEFAULT 0 CHECK (critere_w IN (0,1)),
  critere_m  INTEGER NOT NULL DEFAULT 0 CHECK (critere_m IN (0,1)),
  critere_c  INTEGER NOT NULL DEFAULT 0 CHECK (critere_c IN (0,1)),
  classe_c   TEXT,                       -- C0..C5 si applicable
  critere_s  INTEGER NOT NULL DEFAULT 0 CHECK (critere_s IN (0,1)),
  duree_min  INTEGER NOT NULL CHECK (duree_min IN (15,20,30,45,60,90,120,180,240)),
  sens_feu   TEXT                        -- résumé ; le détail est dans restriction(type 'sens_feu')
);

-- Détails des domaines d'extension (vides au départ, voir docs/EXTENSION_DOMAINES.md)
CREATE TABLE perf_effraction (
  performance_id TEXT PRIMARY KEY REFERENCES performance(id) ON DELETE CASCADE,
  classe_rc      TEXT NOT NULL CHECK (classe_rc IN ('RC1','RC1N','RC2','RC2N','RC3','RC4','RC5','RC6')),
  norme_id       TEXT REFERENCES norme(id),
  duree_resistance_min REAL
);
CREATE TABLE perf_balistique (
  performance_id TEXT PRIMARY KEY REFERENCES performance(id) ON DELETE CASCADE,
  classe         TEXT NOT NULL,          -- 'FB4', 'BR4'
  avec_eclats    TEXT CHECK (avec_eclats IS NULL OR avec_eclats IN ('S','NS')),
  arme_munition  TEXT,
  norme_id       TEXT REFERENCES norme(id)
);
CREATE TABLE perf_aev (
  performance_id TEXT PRIMARY KEY REFERENCES performance(id) ON DELETE CASCADE,
  classe_air     TEXT,                   -- '4'
  classe_eau     TEXT,                   -- '9A', 'E1050'
  classe_vent    TEXT,                   -- 'C3'
  pression_air_pa REAL, pression_eau_pa REAL, pression_vent_pa REAL,
  norme_id       TEXT REFERENCES norme(id)
);
CREATE TABLE perf_acoustique (
  performance_id TEXT PRIMARY KEY REFERENCES performance(id) ON DELETE CASCADE,
  rw_db  REAL NOT NULL, c_db REAL, ctr_db REAL,
  norme_id TEXT REFERENCES norme(id)
);

-- ---------------------------------------------------------------------
-- 6. Dimensions (testé / autorisé toujours séparés via nature_code)
-- ---------------------------------------------------------------------
-- Un « format » regroupe les limites qui s'appliquent ENSEMBLE
-- (ex. L<=1400 ET H<=2500). Les alternatives « OU » = formats distincts
-- avec le même groupe_alternative.
CREATE TABLE dimension_format (
  id                    TEXT PRIMARY KEY,
  document_id           TEXT NOT NULL REFERENCES document(id) ON DELETE CASCADE,
  configuration_id      TEXT REFERENCES configuration(id) ON DELETE CASCADE,
  document_composant_id TEXT REFERENCES document_composant(id) ON DELETE CASCADE, -- ex. vitrage concerné
  objet_code            TEXT NOT NULL REFERENCES ref_objet_dimension(code),
  libelle               TEXT NOT NULL,
  groupe_alternative    TEXT,          -- même valeur = formats alternatifs (« OU »)
  orientation           TEXT CHECK (orientation IS NULL OR orientation IN ('portrait','paysage','indifferent')),
  source_page_id        TEXT REFERENCES source_page(id),
  statut_extraction     TEXT NOT NULL DEFAULT 'extrait' REFERENCES ref_statut_extraction(code)
);

CREATE TABLE dimension (
  id               TEXT PRIMARY KEY,
  format_id        TEXT NOT NULL REFERENCES dimension_format(id) ON DELETE CASCADE,
  grandeur_code    TEXT NOT NULL REFERENCES ref_grandeur(code),
  nature_code      TEXT NOT NULL REFERENCES ref_nature_valeur(code),
  operateur_code   TEXT NOT NULL REFERENCES ref_operateur(code),
  valeur_origine   TEXT NOT NULL,      -- tel qu'écrit : '1610', 'sans limite', '4,54 m²'
  unite_origine    TEXT,               -- tel qu'écrit : 'mm', 'm²'
  valeur_norm      REAL,               -- NULL si sans limite
  unite_norm_code  TEXT REFERENCES ref_unite(code),
  sans_limite      INTEGER NOT NULL DEFAULT 0 CHECK (sans_limite IN (0,1)),
  tolerance_plus   REAL, tolerance_moins REAL,
  statut_extraction TEXT NOT NULL DEFAULT 'extrait' REFERENCES ref_statut_extraction(code),
  CHECK ((sans_limite = 1 AND valeur_norm IS NULL) OR (sans_limite = 0 AND valeur_norm IS NOT NULL) OR statut_extraction <> 'extrait'),
  UNIQUE (format_id, grandeur_code, nature_code, operateur_code)
);

-- ---------------------------------------------------------------------
-- 7. Composants : catalogue de références + occurrences dans les documents
-- ---------------------------------------------------------------------
CREATE TABLE reference_composant (
  id                   TEXT PRIMARY KEY,       -- 'REF-FORSTER-907720'
  reference_normalisee TEXT NOT NULL,          -- sans espaces/points superflus, majuscules
  fabricant_id         TEXT REFERENCES organisme(id),
  categorie_code       TEXT NOT NULL REFERENCES ref_categorie_composant(code),
  designation          TEXT,                   -- désignation générique issue des documents
  UNIQUE (fabricant_id, reference_normalisee)
);

CREATE TABLE reference_alias (
  reference_id TEXT NOT NULL REFERENCES reference_composant(id) ON DELETE CASCADE,
  alias        TEXT NOT NULL,
  type_alias   TEXT NOT NULL CHECK (type_alias IN ('ecriture_document','ancienne_reference','reference_remplacee')),
  document_id  TEXT REFERENCES document(id),
  PRIMARY KEY (reference_id, alias)
);

-- Occurrence d'une référence dans un document (= donnée DOCUMENT).
CREATE TABLE document_composant (
  id                      TEXT PRIMARY KEY,
  document_id             TEXT NOT NULL REFERENCES document(id) ON DELETE CASCADE,
  configuration_id        TEXT REFERENCES configuration(id) ON DELETE CASCADE,
  reference_id            TEXT REFERENCES reference_composant(id),  -- NULL si composant sans référence (« serrure à mortaiser 1 point »)
  reference_brute         TEXT,               -- exactement comme écrit ; NULL si non référencé
  designation_document    TEXT NOT NULL,      -- libellé dans le document
  categorie_code          TEXT NOT NULL REFERENCES ref_categorie_composant(code),
  role_code               TEXT NOT NULL REFERENCES ref_role_composant(code),
  localisation_code       TEXT REFERENCES ref_localisation(code),
  statut_autorisation_code TEXT NOT NULL DEFAULT 'autorise' REFERENCES ref_statut_autorisation(code),
  quantite_min            INTEGER,
  condition_texte         TEXT,               -- condition d'emploi, telle qu'énoncée
  parent_id               TEXT REFERENCES document_composant(id) ON DELETE CASCADE, -- composition (kit -> coffre, gâche)
  role_dans_parent        TEXT,
  source_page_id          TEXT REFERENCES source_page(id),
  statut_extraction       TEXT NOT NULL DEFAULT 'extrait' REFERENCES ref_statut_extraction(code),
  CHECK (reference_brute IS NULL OR reference_brute <> '')
);

-- Caractéristiques atomiques génériques issues du DOCUMENT
CREATE TABLE caracteristique_document (
  id                     TEXT PRIMARY KEY,
  document_composant_id  TEXT NOT NULL REFERENCES document_composant(id) ON DELETE CASCADE,
  type_caracteristique_code TEXT NOT NULL REFERENCES ref_type_caracteristique(code),
  valeur_origine         TEXT NOT NULL,
  valeur_texte           TEXT,
  valeur_num             REAL,
  valeur_bool            INTEGER CHECK (valeur_bool IS NULL OR valeur_bool IN (0,1)),
  unite_origine          TEXT,
  nature_code            TEXT NOT NULL DEFAULT 'nominal' REFERENCES ref_nature_valeur(code),
  source_page_id         TEXT REFERENCES source_page(id),
  UNIQUE (document_composant_id, type_caracteristique_code, valeur_origine)
);

-- Tables typées (1:1 avec document_composant) pour les filtres fins.
CREATE TABLE dc_profile (
  document_composant_id TEXT PRIMARY KEY REFERENCES document_composant(id) ON DELETE CASCADE,
  serie_systeme_id  TEXT REFERENCES systeme(id),
  largeur_mm        REAL,       -- vue (face)
  profondeur_mm     REAL,       -- épaisseur d'ossature
  epaisseur_paroi_mm REAL,
  isole_thermiquement INTEGER CHECK (isole_thermiquement IN (0,1)),
  hauteur_max_emploi_mm REAL,   -- limite d'emploi énoncée (ex. 3000 pour 01.535)
  cote_feu_restriction TEXT     -- ex. 'oppose_feu_uniquement'
);

CREATE TABLE dc_vitrage (
  document_composant_id TEXT PRIMARY KEY REFERENCES document_composant(id) ON DELETE CASCADE,
  gamme             TEXT NOT NULL,            -- 'PYROSWISS', 'PYROSTOP', 'CONTRAFLAM STRUCTURE'
  designation       TEXT NOT NULL,            -- 'Pyrostop 60-101'
  type_vitrage_code TEXT NOT NULL REFERENCES ref_type_vitrage(code),
  epaisseur_mm      REAL,
  epaisseur_min_mm  REAL,
  epaisseur_max_mm  REAL,
  classe_nominale   TEXT,                     -- tel qu'affiché dans le nom commercial ('E30', 'EW30', '60')
  intercalaire_min_mm REAL,
  intercalaire_max_mm REAL,
  composition_detaillee_disponible INTEGER CHECK (composition_detaillee_disponible IN (0,1)) -- 0 = « en possession du laboratoire »
);

CREATE TABLE dc_serrure (
  document_composant_id TEXT PRIMARY KEY REFERENCES document_composant(id) ON DELETE CASCADE,
  type_serrure_code TEXT NOT NULL REFERENCES ref_type_serrure(code),
  fonction_code     TEXT REFERENCES ref_fonction_serrure(code),
  nb_points         INTEGER CHECK (nb_points IS NULL OR nb_points BETWEEN 1 AND 3),
  point_haut        INTEGER CHECK (point_haut IN (0,1)),
  point_median      INTEGER CHECK (point_median IN (0,1)),
  point_bas         INTEGER CHECK (point_bas IN (0,1)),
  antipanique       INTEGER CHECK (antipanique IN (0,1)),
  main_din          TEXT CHECK (main_din IS NULL OR main_din IN ('G','D','reversible')),
  entraxe_mm        REAL,
  type_commande     TEXT CHECK (type_commande IS NULL OR type_commande IN ('mecanique','electrique','motorisee','das_electrique','thermique')),
  version           TEXT CHECK (version IS NULL OR version IN ('classique','push_bar')),
  seuil_temperature_c REAL,
  position_depuis_bas_mm REAL,
  position_depuis_haut_mm REAL,
  vantail           TEXT CHECK (vantail IS NULL OR vantail IN ('unique','principal','secondaire','tous'))
);

CREATE TABLE dc_articulation (
  document_composant_id TEXT PRIMARY KEY REFERENCES document_composant(id) ON DELETE CASCADE,
  type_articulation_code TEXT NOT NULL REFERENCES ref_type_articulation(code),
  mode_fixation     TEXT CHECK (mode_fixation IS NULL OR mode_fixation IN ('souder','visser','encastrer','sceller')),
  reglage           TEXT CHECK (reglage IS NULL OR reglage IN ('2D','3D')),
  distance_extremite_mm REAL,
  position          TEXT          -- 'mi_hauteur', 'haut_bas'
);

CREATE TABLE dc_ferme_porte (
  document_composant_id TEXT PRIMARY KEY REFERENCES document_composant(id) ON DELETE CASCADE,
  type_ferme_porte_code TEXT NOT NULL REFERENCES ref_type_ferme_porte(code),
  cote_feu_autorise   INTEGER CHECK (cote_feu_autorise IN (0,1)),
  cote_oppose_autorise INTEGER CHECK (cote_oppose_autorise IN (0,1)),
  protection_requise  TEXT,       -- ex. 'plaque PROMATECT H ou SUPALUX 10 mm'
  force_en            TEXT,       -- 'EN 2-4'
  largeur_vantail_max_mm REAL,
  poids_vantail_max_kg   REAL,
  angle_ouverture_max_deg REAL
);

CREATE TABLE dc_joint (
  document_composant_id TEXT PRIMARY KEY REFERENCES document_composant(id) ON DELETE CASCADE,
  type_joint_code   TEXT NOT NULL REFERENCES ref_type_joint(code),
  largeur_mm        REAL,
  epaisseur_mm      REAL,
  epaisseur_min_mm  REAL,
  epaisseur_max_mm  REAL,
  position          TEXT CHECK (position IS NULL OR position IN ('fond_feuillure','ailette','parclose','battement','peripherie','jonction_vitrages','tranche_vitrage')),
  marque_produit    TEXT          -- ex. 'PALSTOP P (BRANDDEX)'
);

CREATE TABLE dc_fixation (
  document_composant_id TEXT PRIMARY KEY REFERENCES document_composant(id) ON DELETE CASCADE,
  type_fixation_code TEXT NOT NULL REFERENCES ref_type_fixation(code),
  diametre_mm       REAL,
  longueur_mm       REAL,
  pas_max_mm        REAL,
  distance_angle_mm REAL,
  support_cible     TEXT
);

-- ---------------------------------------------------------------------
-- 8. Mise en œuvre, domaine d'application, restrictions
-- ---------------------------------------------------------------------
CREATE TABLE support_pose (
  id                   TEXT PRIMARY KEY,
  document_id          TEXT NOT NULL REFERENCES document(id) ON DELETE CASCADE,
  configuration_id     TEXT REFERENCES configuration(id) ON DELETE CASCADE,
  type_support_code    TEXT NOT NULL REFERENCES ref_type_support(code),
  masse_vol_min_kg_m3  REAL,
  masse_vol_operateur_code TEXT REFERENCES ref_operateur(code),
  epaisseur_min_mm     REAL,
  epaisseur_operateur_code TEXT REFERENCES ref_operateur(code),
  classement_pv_exige  TEXT,            -- ex. 'EI 60'
  prolongation_laterale INTEGER CHECK (prolongation_laterale IN (0,1)),
  imposte_autorisee    INTEGER CHECK (imposte_autorisee IN (0,1)),
  allege_autorisee     INTEGER CHECK (allege_autorisee IN (0,1)),
  pas_fixation_max_mm  REAL,
  condition_texte      TEXT,
  source_page_id       TEXT REFERENCES source_page(id)
);

CREATE TABLE restriction (
  id                    TEXT PRIMARY KEY,
  document_id           TEXT NOT NULL REFERENCES document(id) ON DELETE CASCADE,
  configuration_id      TEXT REFERENCES configuration(id) ON DELETE CASCADE,
  document_composant_id TEXT REFERENCES document_composant(id) ON DELETE CASCADE,
  type_code             TEXT NOT NULL REFERENCES ref_type_restriction(code),
  libelle               TEXT NOT NULL,          -- résumé filtrable
  texte_source          TEXT,                   -- extrait court du document
  source_page_id        TEXT REFERENCES source_page(id)
);

-- ---------------------------------------------------------------------
-- 9. Enrichissement externe (strictement séparé)
-- ---------------------------------------------------------------------
CREATE TABLE enrichissement_externe (
  id                        TEXT PRIMARY KEY,
  reference_id              TEXT NOT NULL REFERENCES reference_composant(id) ON DELETE CASCADE,
  type_caracteristique_code TEXT NOT NULL REFERENCES ref_type_caracteristique(code),
  valeur_texte              TEXT,
  valeur_num                REAL,
  valeur_bool               INTEGER CHECK (valeur_bool IS NULL OR valeur_bool IN (0,1)),
  unite_code                TEXT REFERENCES ref_unite(code),
  source                    TEXT NOT NULL DEFAULT 'enrichissement' CHECK (source = 'enrichissement'),
  source_libelle            TEXT NOT NULL,
  source_url                TEXT,
  date_recherche            TEXT NOT NULL,
  statut_fiabilite_code     TEXT NOT NULL REFERENCES ref_statut_fiabilite(code),
  commentaire               TEXT,
  CHECK (valeur_texte IS NOT NULL OR valeur_num IS NOT NULL OR valeur_bool IS NOT NULL)
);

-- ---------------------------------------------------------------------
-- 10. Contrôle qualité / points de contrôle humain
-- ---------------------------------------------------------------------
CREATE TABLE controle_humain (
  id           TEXT PRIMARY KEY,
  document_id  TEXT REFERENCES document(id) ON DELETE CASCADE,
  table_cible  TEXT,
  ligne_id     TEXT,
  type_code    TEXT NOT NULL REFERENCES ref_type_controle(code),
  description  TEXT NOT NULL,
  statut       TEXT NOT NULL DEFAULT 'ouvert' CHECK (statut IN ('ouvert','resolu','abandonne')),
  resolution   TEXT,
  source_page_id TEXT REFERENCES source_page(id)
);

-- ---------------------------------------------------------------------
-- 11. Index plein texte simple (LIKE) — portable dans toute build sql.js
-- ---------------------------------------------------------------------
CREATE TABLE recherche_index (
  objet_type  TEXT NOT NULL,
  objet_id    TEXT NOT NULL,
  document_id TEXT REFERENCES document(id) ON DELETE CASCADE,
  texte       TEXT NOT NULL,              -- minuscules, sans accents
  PRIMARY KEY (objet_type, objet_id)
);

-- =====================================================================
-- INDEX (tous les champs de filtre / jointure)
-- =====================================================================
CREATE INDEX ix_document_type        ON document(type_code);
CREATE INDEX ix_document_domaine     ON document(domaine_code);
CREATE INDEX ix_document_validite    ON document(date_validite);
CREATE INDEX ix_document_emission    ON document(date_emission);
CREATE INDEX ix_document_fichier     ON document(fichier_source_id);
CREATE INDEX ix_document_labo        ON document(laboratoire_id);
CREATE INDEX ix_source_page_doc      ON source_page(document_id);
CREATE INDEX ix_relation_source      ON document_relation(document_source_id, type_relation_code);
CREATE INDEX ix_relation_cible       ON document_relation(document_cible_id, type_relation_code);
CREATE INDEX ix_docorg_org           ON document_organisme(organisme_id, role_code);
CREATE INDEX ix_docnorme_norme       ON document_norme(norme_id);
CREATE INDEX ix_docessai_essai       ON document_essai(essai_id);
CREATE INDEX ix_essai_res_essai      ON essai_resultat(essai_id, critere_code);
CREATE INDEX ix_docsys_sys           ON document_systeme(systeme_id);
CREATE INDEX ix_config_doc           ON configuration(document_id);
CREATE INDEX ix_config_typo          ON configuration(typologie_code);
CREATE INDEX ix_config_sys           ON configuration(systeme_id);
CREATE INDEX ix_config_vantaux       ON configuration(nb_vantaux_min, nb_vantaux_max);
CREATE INDEX ix_perf_doc             ON performance(document_id);
CREATE INDEX ix_perf_config          ON performance(configuration_id);
CREATE INDEX ix_perf_domaine_classe  ON performance(domaine_code, classe_normalisee);
CREATE INDEX ix_perf_feu_duree       ON perf_feu(duree_min, critere_i, critere_w);
CREATE INDEX ix_dimfmt_doc           ON dimension_format(document_id);
CREATE INDEX ix_dimfmt_config        ON dimension_format(configuration_id);
CREATE INDEX ix_dimfmt_dc            ON dimension_format(document_composant_id);
CREATE INDEX ix_dimfmt_objet         ON dimension_format(objet_code);
CREATE INDEX ix_dim_format           ON dimension(format_id);
CREATE INDEX ix_dim_filtre           ON dimension(grandeur_code, nature_code, valeur_norm);
CREATE INDEX ix_ref_norm             ON reference_composant(reference_normalisee);
CREATE INDEX ix_ref_cat              ON reference_composant(categorie_code);
CREATE INDEX ix_ref_fab              ON reference_composant(fabricant_id);
CREATE INDEX ix_alias_alias          ON reference_alias(alias);
CREATE INDEX ix_dc_doc               ON document_composant(document_id);
CREATE INDEX ix_dc_config            ON document_composant(configuration_id);
CREATE INDEX ix_dc_ref               ON document_composant(reference_id);
CREATE INDEX ix_dc_brute             ON document_composant(reference_brute);
CREATE INDEX ix_dc_cat_role          ON document_composant(categorie_code, role_code);
CREATE INDEX ix_dc_parent            ON document_composant(parent_id);
CREATE INDEX ix_dc_statut            ON document_composant(statut_autorisation_code);
CREATE INDEX ix_carac_dc             ON caracteristique_document(document_composant_id);
CREATE INDEX ix_carac_type_val       ON caracteristique_document(type_caracteristique_code, valeur_num);
CREATE INDEX ix_carac_type_txt       ON caracteristique_document(type_caracteristique_code, valeur_texte);
CREATE INDEX ix_vitrage_gamme        ON dc_vitrage(gamme, type_vitrage_code);
CREATE INDEX ix_vitrage_ep           ON dc_vitrage(epaisseur_mm);
CREATE INDEX ix_serrure_filtre       ON dc_serrure(type_serrure_code, fonction_code, nb_points, antipanique, main_din);
CREATE INDEX ix_artic_filtre         ON dc_articulation(type_articulation_code, mode_fixation, reglage);
CREATE INDEX ix_fp_filtre            ON dc_ferme_porte(type_ferme_porte_code);
CREATE INDEX ix_joint_filtre         ON dc_joint(type_joint_code, largeur_mm, epaisseur_mm);
CREATE INDEX ix_profile_sys          ON dc_profile(serie_systeme_id);
CREATE INDEX ix_fix_type             ON dc_fixation(type_fixation_code);
CREATE INDEX ix_support_doc          ON support_pose(document_id);
CREATE INDEX ix_support_type         ON support_pose(type_support_code);
CREATE INDEX ix_restr_doc            ON restriction(document_id);
CREATE INDEX ix_restr_type           ON restriction(type_code);
CREATE INDEX ix_restr_dc             ON restriction(document_composant_id);
CREATE INDEX ix_enrich_ref           ON enrichissement_externe(reference_id, type_caracteristique_code);
CREATE INDEX ix_enrich_statut        ON enrichissement_externe(statut_fiabilite_code);
CREATE INDEX ix_controle_doc         ON controle_humain(document_id, statut);
CREATE INDEX ix_recherche_doc        ON recherche_index(document_id);

-- =====================================================================
-- VUES (prêtes pour l'application)
-- =====================================================================

-- PV principal -> date de validité effective (dernière reconduction présente)
CREATE VIEW v_validite_effective AS
SELECT d.id AS document_id,
       d.numero_normalise,
       d.date_validite AS date_validite_initiale,
       COALESCE((SELECT MAX(r.date_validite)
                   FROM document_relation dr
                   JOIN document r ON r.id = dr.document_source_id
                  WHERE dr.document_cible_id = d.id
                    AND dr.type_relation_code = 'reconduit'), d.date_validite) AS date_validite_effective,
       (SELECT r.numero_normalise
          FROM document_relation dr JOIN document r ON r.id = dr.document_source_id
         WHERE dr.document_cible_id = d.id AND dr.type_relation_code = 'reconduit'
         ORDER BY r.date_validite DESC LIMIT 1) AS derniere_reconduction
  FROM document d
 WHERE d.type_code IN ('pv_classement');

-- Document « de rattachement » : extensions/reconductions -> PV principal(aux).
-- Une extension multiple produit une ligne par PV étendu.
CREATE VIEW v_document_rattachement AS
SELECT d.id AS document_id, d.id AS pv_principal_id
  FROM document d
 WHERE d.id NOT IN (SELECT document_source_id FROM document_relation WHERE type_relation_code IN ('etend','reconduit'))
UNION
SELECT dr.document_source_id, dr.document_cible_id
  FROM document_relation dr
 WHERE dr.type_relation_code IN ('etend','reconduit');

-- Classements feu à plat
CREATE VIEW v_classement_feu AS
SELECT p.id AS performance_id, p.document_id, d.numero_normalise, d.type_code,
       p.configuration_id, c.libelle AS configuration, c.typologie_code, s.nom AS systeme,
       p.classe_normalisee, f.duree_min, f.critere_e, f.critere_i, f.variante_i, f.critere_w,
       f.sens_feu, p.condition_texte, sp.page_doc, sp.section
  FROM performance p
  JOIN perf_feu f      ON f.performance_id = p.id
  JOIN document d      ON d.id = p.document_id
  LEFT JOIN configuration c ON c.id = p.configuration_id
  LEFT JOIN systeme s  ON s.id = c.systeme_id
  LEFT JOIN source_page sp ON sp.id = p.source_page_id;

-- Composants à plat (document + référence + page)
CREATE VIEW v_composant AS
SELECT dc.id AS document_composant_id, dc.document_id, d.numero_normalise,
       dc.configuration_id, dc.reference_brute, rc.reference_normalisee,
       o.nom AS fabricant, dc.categorie_code, dc.role_code, dc.localisation_code,
       dc.statut_autorisation_code, dc.designation_document, dc.condition_texte,
       dc.parent_id, dc.role_dans_parent, sp.page_doc, sp.section, sp.planche,
       dc.statut_extraction
  FROM document_composant dc
  JOIN document d ON d.id = dc.document_id
  LEFT JOIN reference_composant rc ON rc.id = dc.reference_id
  LEFT JOIN organisme o ON o.id = rc.fabricant_id
  LEFT JOIN source_page sp ON sp.id = dc.source_page_id;

-- Limites dimensionnelles autorisées (max) à plat
CREATE VIEW v_dimension AS
SELECT df.id AS format_id, df.document_id, d.numero_normalise, df.configuration_id,
       df.document_composant_id, df.objet_code, df.libelle, df.groupe_alternative,
       dm.grandeur_code, dm.nature_code, dm.operateur_code, dm.valeur_origine,
       dm.unite_origine, dm.valeur_norm, dm.unite_norm_code, dm.sans_limite,
       dm.statut_extraction, sp.page_doc, sp.section
  FROM dimension_format df
  JOIN dimension dm ON dm.format_id = df.id
  JOIN document d ON d.id = df.document_id
  LEFT JOIN source_page sp ON sp.id = df.source_page_id;

-- Fiche référence : données document vs enrichissement (jamais fusionnées)
CREATE VIEW v_reference_fiche AS
SELECT rc.id AS reference_id, rc.reference_normalisee, 'document' AS source,
       cd.type_caracteristique_code AS caracteristique,
       COALESCE(cd.valeur_texte, CAST(cd.valeur_num AS TEXT), CAST(cd.valeur_bool AS TEXT)) AS valeur,
       NULL AS statut_fiabilite, d.numero_normalise AS origine
  FROM reference_composant rc
  JOIN document_composant dc ON dc.reference_id = rc.id
  JOIN caracteristique_document cd ON cd.document_composant_id = dc.id
  JOIN document d ON d.id = dc.document_id
UNION ALL
SELECT rc.id, rc.reference_normalisee, 'enrichissement',
       e.type_caracteristique_code,
       COALESCE(e.valeur_texte, CAST(e.valeur_num AS TEXT), CAST(e.valeur_bool AS TEXT)),
       e.statut_fiabilite_code, e.source_libelle
  FROM reference_composant rc
  JOIN enrichissement_externe e ON e.reference_id = rc.id;
