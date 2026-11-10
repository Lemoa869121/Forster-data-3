-- Requêtes de filtre représentatives — exécutables telles quelles dans sql.js
-- Paramètres nommés (:param) : stmt.bind({':param': valeur}) en JS.
-- Format lu par scripts/test_queries.py : bloc « -- name: », « -- params: <json> », SQL jusqu'au « ; ».

-- name: Q01_recherche_reference
-- desc: Toutes les occurrences d'une référence (exacte ou partielle, normalisée ou alias) avec PV de rattachement et validité effective
-- params: {":ref": "907724"}
WITH q AS (SELECT upper(replace(replace(:ref,' ',''),'.','')) AS r)
SELECT d.numero_normalise AS document, d.type_code, pv.numero_normalise AS pv_principal,
       ve.date_validite_effective, dc.reference_brute, rc.reference_normalisee, o.nom AS fabricant,
       dc.categorie_code, dc.role_code, dc.localisation_code, dc.statut_autorisation_code,
       dc.designation_document, c.libelle AS configuration, sp.page_doc, sp.section, sp.planche, dc.statut_extraction
FROM document_composant dc
JOIN q
LEFT JOIN reference_composant rc ON rc.id = dc.reference_id
LEFT JOIN organisme o ON o.id = rc.fabricant_id
JOIN document d ON d.id = dc.document_id
JOIN v_document_rattachement ra ON ra.document_id = d.id
JOIN document pv ON pv.id = ra.pv_principal_id
LEFT JOIN v_validite_effective ve ON ve.document_id = pv.id
LEFT JOIN configuration c ON c.id = dc.configuration_id
LEFT JOIN source_page sp ON sp.id = dc.source_page_id
WHERE rc.reference_normalisee LIKE '%' || q.r || '%'
   OR dc.reference_id IN (SELECT reference_id FROM reference_alias WHERE upper(replace(replace(alias,' ',''),'.','')) LIKE '%' || q.r || '%')
ORDER BY pv.numero_normalise, d.numero_normalise;

-- name: Q02_serrures_par_fonction
-- desc: Serrures / kits par fonction, nombre de points, antipanique, main DIN et vantail (NULL = pas de filtre)
-- params: {":fonction": "E", ":nb_points": 2, ":antipanique": 1, ":main": null, ":vantail": null}
SELECT d.numero_normalise AS document, dc.reference_brute, s.type_serrure_code, s.fonction_code, s.nb_points,
       s.point_haut, s.point_median, s.point_bas, s.antipanique, s.main_din, s.version, s.vantail,
       (SELECT group_concat(e.role_dans_parent || '=' || e.reference_brute, ' ; ') FROM document_composant e WHERE e.parent_id = dc.id) AS composition,
       c.libelle AS configuration, sp.planche, sp.page_doc, dc.statut_extraction
FROM dc_serrure s
JOIN document_composant dc ON dc.id = s.document_composant_id
JOIN document d ON d.id = dc.document_id
LEFT JOIN configuration c ON c.id = dc.configuration_id
LEFT JOIN source_page sp ON sp.id = dc.source_page_id
WHERE (:fonction IS NULL OR s.fonction_code = :fonction)
  AND (:nb_points IS NULL OR s.nb_points = :nb_points)
  AND (:antipanique IS NULL OR s.antipanique = :antipanique)
  AND (:main IS NULL OR s.main_din = :main)
  AND (:vantail IS NULL OR s.vantail = :vantail)
ORDER BY d.numero_normalise, s.main_din, dc.reference_brute;

-- name: Q03_documents_par_systeme
-- desc: Documents (PV + extensions) concernant un système Forster, avec classements et validité effective
-- params: {":systeme": "FUEGO LIGHT 30"}
SELECT s.nom AS systeme, ds.role, d.numero_normalise, d.type_code, d.objet,
       (SELECT group_concat(DISTINCT p.classe_normalisee) FROM performance p WHERE p.document_id = d.id) AS classements,
       ve.date_validite_effective, ve.derniere_reconduction
FROM document_systeme ds
JOIN systeme s ON s.id = ds.systeme_id
JOIN document d ON d.id = ds.document_id
LEFT JOIN v_validite_effective ve ON ve.document_id = d.id
WHERE s.nom_normalise = upper(:systeme)
ORDER BY d.date_emission;

-- name: Q04_par_performance
-- desc: Configurations classées au moins à une durée donnée pour une combinaison de critères (ex. EI ≥ 60)
-- params: {":duree_min": 60, ":exige_i": 1, ":exige_w": 0, ":typologie": null}
SELECT v.numero_normalise AS document, v.configuration, v.typologie_code, v.systeme, v.classe_normalisee,
       v.duree_min, v.condition_texte, v.page_doc, v.section, ve.date_validite_effective
FROM v_classement_feu v
JOIN v_document_rattachement ra ON ra.document_id = v.document_id
LEFT JOIN v_validite_effective ve ON ve.document_id = ra.pv_principal_id
WHERE v.duree_min >= :duree_min
  AND (:exige_i = 0 OR v.critere_i = 1)
  AND (:exige_w = 0 OR v.critere_w = 1)
  AND (:typologie IS NULL OR v.typologie_code = :typologie)
ORDER BY v.duree_min DESC, v.numero_normalise;

-- name: Q05_passage_libre_minimal
-- desc: Blocs-portes dont le passage libre / vantail autorisé atteint au moins L x H demandés (valeurs AUTORISÉES uniquement)
-- params: {":largeur": 1400, ":hauteur": 2500}
SELECT df.document_id, d.numero_normalise, df.objet_code, df.libelle, c.libelle AS configuration,
       MAX(CASE WHEN dm.grandeur_code='largeur' AND dm.nature_code='autorise_max' THEN coalesce(dm.valeur_norm, 1e9) END) AS largeur_max,
       MAX(CASE WHEN dm.grandeur_code='hauteur' AND dm.nature_code='autorise_max' THEN coalesce(dm.valeur_norm, 1e9) END) AS hauteur_max,
       MAX(CASE WHEN dm.grandeur_code='surface' AND dm.nature_code='autorise_max' THEN dm.valeur_norm END) AS surface_max_m2,
       sp.page_doc, sp.section
FROM dimension_format df
JOIN dimension dm ON dm.format_id = df.id
JOIN document d ON d.id = df.document_id
LEFT JOIN configuration c ON c.id = df.configuration_id
LEFT JOIN source_page sp ON sp.id = df.source_page_id
WHERE df.objet_code IN ('passage_libre','vantail_hors_tout')
GROUP BY df.id
HAVING largeur_max >= :largeur AND hauteur_max >= :hauteur
   AND (surface_max_m2 IS NULL OR surface_max_m2 >= (:largeur * :hauteur) / 1e6)
ORDER BY d.numero_normalise;

-- name: Q06_vitrage_dimension
-- desc: Vitrages dont UN format autorisé couvre L x H (gère portrait/paysage et surface max)
-- params: {":largeur": 1500, ":hauteur": 2500, ":gamme": null}
SELECT d.numero_normalise AS document, v.gamme, v.designation, v.type_vitrage_code, df.libelle AS format,
       MAX(CASE WHEN dm.grandeur_code='largeur' AND dm.nature_code='autorise_max' THEN dm.valeur_norm END) AS l_max,
       MAX(CASE WHEN dm.grandeur_code='hauteur' AND dm.nature_code='autorise_max' THEN dm.valeur_norm END) AS h_max,
       MAX(CASE WHEN dm.grandeur_code='surface' AND dm.nature_code='autorise_max' THEN dm.valeur_norm END) AS s_max,
       df.objet_code, df.statut_extraction, sp.page_doc, sp.section
FROM dimension_format df
JOIN dc_vitrage v ON v.document_composant_id = df.document_composant_id
JOIN dimension dm ON dm.format_id = df.id
JOIN document d ON d.id = df.document_id
LEFT JOIN source_page sp ON sp.id = df.source_page_id
WHERE df.objet_code IN ('vitrage_hors_tout','vitrage_clair')
  AND (:gamme IS NULL OR v.gamme LIKE '%' || :gamme || '%')
GROUP BY df.id
HAVING l_max >= :largeur AND h_max >= :hauteur AND (s_max IS NULL OR s_max >= (:largeur * :hauteur) / 1e6)
ORDER BY d.numero_normalise, v.designation;

-- name: Q07_contenu_fichier_source
-- desc: Inventaire d'un fichier PDF source : documents logiques, ordre, pages, statut
-- params: {":fichier": "FIC-11-A-507"}
SELECT f.nom_fichier, d.ordre_dans_fichier, d.numero, d.type_code, d.date_emission, d.date_validite, d.nb_pages, d.statut_extraction,
       (SELECT count(*) FROM document_composant dc WHERE dc.document_id = d.id) AS nb_composants,
       (SELECT count(*) FROM dimension_format x WHERE x.document_id = d.id) AS nb_formats_dim
FROM document d JOIN fichier_source f ON f.id = d.fichier_source_id
WHERE f.id = :fichier
ORDER BY d.ordre_dans_fichier;

-- name: Q08_documents_lies_a_un_pv
-- desc: Extensions, reconductions, remplacements et règles de cumul autour d'un PV principal
-- params: {":pv": "11-A-507"}
SELECT pv.numero_normalise AS pv, dr.type_relation_code, src.numero_normalise AS document_source, src.type_code AS type_source,
       cib.numero_normalise AS document_cible, src.date_emission, src.date_validite, src.present_dans_corpus,
       dr.commentaire
FROM document pv
JOIN document_relation dr ON dr.document_cible_id = pv.id OR dr.document_source_id = pv.id
   OR dr.document_source_id IN (SELECT r.document_source_id FROM document_relation r WHERE r.document_cible_id = pv.id AND r.type_relation_code IN ('etend','reconduit'))
JOIN document src ON src.id = dr.document_source_id
JOIN document cib ON cib.id = dr.document_cible_id
WHERE pv.numero_normalise = :pv AND pv.type_code = 'pv_classement'
ORDER BY src.date_emission, dr.type_relation_code;

-- name: Q09_restrictions_applicables
-- desc: Restrictions d'un PV et de ses extensions, filtrables par type
-- params: {":pv": "EFR-24-000553", ":type": null}
SELECT d.numero_normalise AS document, r.type_code, r.libelle, r.texte_source, c.libelle AS configuration,
       dc.reference_brute AS composant, sp.page_doc, sp.section
FROM restriction r
JOIN document d ON d.id = r.document_id
JOIN v_document_rattachement ra ON ra.document_id = d.id
JOIN document pv ON pv.id = ra.pv_principal_id
LEFT JOIN configuration c ON c.id = r.configuration_id
LEFT JOIN document_composant dc ON dc.id = r.document_composant_id
LEFT JOIN source_page sp ON sp.id = r.source_page_id
WHERE pv.numero_normalise = :pv AND (:type IS NULL OR r.type_code = :type)
ORDER BY r.type_code, d.numero_normalise;

-- name: Q10_paumelles
-- desc: Articulations par type, mode de fixation et réglage
-- params: {":mode": "visser", ":reglage": "3D"}
SELECT d.numero_normalise AS document, dc.reference_brute, a.type_articulation_code, a.mode_fixation, a.reglage,
       a.distance_extremite_mm, dc.condition_texte, sp.page_doc, sp.section
FROM dc_articulation a
JOIN document_composant dc ON dc.id = a.document_composant_id
JOIN document d ON d.id = dc.document_id
LEFT JOIN source_page sp ON sp.id = dc.source_page_id
WHERE (:mode IS NULL OR a.mode_fixation = :mode) AND (:reglage IS NULL OR a.reglage = :reglage)
ORDER BY d.numero_normalise, dc.reference_brute;

-- name: Q11_ferme_portes_cote_oppose
-- desc: Ferme-portes autorisés côté opposé au feu (et protection exigée) — NULL = non précisé par le document
-- params: {}
SELECT d.numero_normalise AS document, dc.reference_brute, o.nom AS fabricant, f.type_ferme_porte_code,
       f.cote_feu_autorise, f.cote_oppose_autorise, f.protection_requise, sp.page_doc, dc.statut_extraction
FROM dc_ferme_porte f
JOIN document_composant dc ON dc.id = f.document_composant_id
JOIN document d ON d.id = dc.document_id
LEFT JOIN reference_composant rc ON rc.id = dc.reference_id
LEFT JOIN organisme o ON o.id = rc.fabricant_id
LEFT JOIN source_page sp ON sp.id = dc.source_page_id
WHERE f.cote_oppose_autorise = 1
ORDER BY d.numero_normalise, dc.reference_brute;

-- name: Q12_pv_valides_a_date
-- desc: PV principaux valides à une date (dernière reconduction présente dans le corpus)
-- params: {":date": "2026-11-10"}
SELECT ve.numero_normalise, ve.date_validite_initiale, ve.date_validite_effective, ve.derniere_reconduction, d.objet
FROM v_validite_effective ve JOIN document d ON d.id = ve.document_id
WHERE d.present_dans_corpus = 1 AND ve.date_validite_effective >= :date
ORDER BY ve.date_validite_effective;

-- name: Q13_recherche_texte
-- desc: Recherche libre insensible à la casse/aux accents (mots normalisés côté appli)
-- params: {":texte": "antipanique"}
SELECT ri.objet_type, ri.objet_id, d.numero_normalise, substr(ri.texte, 1, 160) AS extrait
FROM recherche_index ri LEFT JOIN document d ON d.id = ri.document_id
WHERE ri.texte LIKE '%' || lower(:texte) || '%'
ORDER BY d.numero_normalise LIMIT 200;

-- name: Q14_fiche_reference
-- desc: Fiche d'une référence : données document et données d'enrichissement, jamais fusionnées
-- params: {":ref": "HZ43F"}
SELECT * FROM v_reference_fiche WHERE reference_normalisee = upper(replace(replace(:ref,' ',''),'.',''))
UNION ALL
SELECT rc.id, rc.reference_normalisee, 'document', 'occurrence', dc.designation_document || ' [' || dc.statut_autorisation_code || ']', NULL, d.numero_normalise
FROM reference_composant rc JOIN document_composant dc ON dc.reference_id = rc.id JOIN document d ON d.id = dc.document_id
WHERE rc.reference_normalisee = upper(replace(replace(:ref,' ',''),'.',''));

-- name: Q15_controles_ouverts
-- desc: Points de contrôle humain ouverts par document
-- params: {":type": null}
SELECT d.numero_normalise, ch.type_code, ch.description, sp.page_doc, sp.section, sp.planche
FROM controle_humain ch LEFT JOIN document d ON d.id = ch.document_id LEFT JOIN source_page sp ON sp.id = ch.source_page_id
WHERE ch.statut = 'ouvert' AND (:type IS NULL OR ch.type_code = :type)
ORDER BY d.numero_normalise;

-- name: Q16_essais_justificatifs
-- desc: Essais cités et VALEURS TESTÉES (minutes) — distinctes des classements
-- params: {":pv": "11-A-507"}
SELECT d.numero_normalise AS document, e.reference AS essai, o.nom AS laboratoire, n.code || coalesce(':' || n.annee, '') || coalesce(n.amendement, '') AS norme,
       er.critere_code, er.operateur_code, er.duree_min, er.condition_essai
FROM document_essai de
JOIN document d ON d.id = de.document_id
JOIN v_document_rattachement ra ON ra.document_id = d.id
JOIN document pv ON pv.id = ra.pv_principal_id
JOIN essai e ON e.id = de.essai_id
LEFT JOIN organisme o ON o.id = e.laboratoire_id
LEFT JOIN norme n ON n.id = e.norme_id
LEFT JOIN essai_resultat er ON er.essai_id = e.id
WHERE pv.numero_normalise = :pv
ORDER BY d.numero_normalise, e.reference, er.critere_code;

-- name: Q17_joints
-- desc: Joints par type et section
-- params: {":type": "fibre_minerale", ":epaisseur": 5}
SELECT d.numero_normalise, dc.reference_brute, j.type_joint_code, j.largeur_mm, j.epaisseur_mm, j.epaisseur_min_mm, j.epaisseur_max_mm, j.position, j.marque_produit
FROM dc_joint j JOIN document_composant dc ON dc.id = j.document_composant_id JOIN document d ON d.id = dc.document_id
WHERE (:type IS NULL OR j.type_joint_code = :type)
  AND (:epaisseur IS NULL OR j.epaisseur_mm = :epaisseur OR (:epaisseur BETWEEN j.epaisseur_min_mm AND j.epaisseur_max_mm))
ORDER BY d.numero_normalise, dc.reference_brute;

-- name: Q18_supports
-- desc: Documents autorisant un type de construction support (ex. cloison 98/48 avec allège)
-- params: {":type_support": "cloison_legere_98_48", ":allege": 1}
SELECT d.numero_normalise, s.type_support_code, s.masse_vol_min_kg_m3, s.epaisseur_min_mm, s.classement_pv_exige,
       s.prolongation_laterale, s.imposte_autorisee, s.allege_autorisee, s.pas_fixation_max_mm, s.condition_texte, sp.page_doc, sp.section
FROM support_pose s JOIN document d ON d.id = s.document_id LEFT JOIN source_page sp ON sp.id = s.source_page_id
WHERE s.type_support_code = :type_support AND (:allege IS NULL OR s.allege_autorisee = :allege)
ORDER BY d.numero_normalise;

-- name: Q19_filtre_combine
-- desc: Filtre combiné : typologie + classe minimale + présence d'un composant (référence) dans le même PV (ou ses extensions)
-- params: {":typologie": "bloc_porte", ":duree_min": 30, ":ref": "TS93"}
SELECT DISTINCT pv.numero_normalise AS pv, v.classe_normalisee, v.configuration, ve.date_validite_effective,
       dc.reference_brute, d2.numero_normalise AS document_composant
FROM v_classement_feu v
JOIN v_document_rattachement ra ON ra.document_id = v.document_id
JOIN document pv ON pv.id = ra.pv_principal_id
LEFT JOIN v_validite_effective ve ON ve.document_id = pv.id
JOIN v_document_rattachement ra2 ON ra2.pv_principal_id = pv.id
JOIN document_composant dc ON dc.document_id = ra2.document_id
JOIN document d2 ON d2.id = dc.document_id
JOIN reference_composant rc ON rc.id = dc.reference_id
WHERE v.typologie_code = :typologie AND v.duree_min >= :duree_min
  AND rc.reference_normalisee = upper(replace(replace(:ref,' ',''),'.',''))
ORDER BY pv.numero_normalise;

-- name: Q20_valeurs_testees_vs_autorisees
-- desc: Contrôle : aucune dimension ne mélange natures ; répartition des natures de valeurs
-- params: {}
SELECT nature_code, grandeur_code, count(*) AS n FROM dimension GROUP BY nature_code, grandeur_code ORDER BY nature_code, grandeur_code;
