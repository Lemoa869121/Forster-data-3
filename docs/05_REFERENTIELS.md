# 7. Référentiels contrôlés

Tables `ref_*` — valeurs initiales dans `db/referentiels.sql`. Toute colonne `*_code` du schéma pointe vers l'une d'elles (clé étrangère).

## `ref_categorie_composant`

| code | libelle | famille | description |
|---|---|---|---|
| profile | Profilé | profiles |  |
| tube_acier | Tube / plat acier | profiles |  |
| manchon | Manchon d'assemblage | profiles |  |
| vitrage | Vitrage | remplissages |  |
| panneau | Panneau plein | remplissages |  |
| film_adhesif | Film adhésif | remplissages |  |
| parclose | Parclose | maintien_vitrage |  |
| vis_bouton | Vis bouton / bouton de parclose | maintien_vitrage |  |
| ressort_parclose | Ressort de parclose | maintien_vitrage |  |
| serreur | Serreur / profil de serrage | maintien_vitrage |  |
| support_verre | Support de verre / base de serrage | maintien_vitrage |  |
| distanceur | Distanceur | maintien_vitrage |  |
| cale | Cale de vitrage | cales |  |
| joint_intumescent | Joint / bande intumescent(e) | joints |  |
| joint_epdm | Joint EPDM | joints |  |
| joint_cr | Joint CR | joints |  |
| joint_butee | Joint de butée | joints |  |
| bande_fibre | Bande de fibre minérale | joints |  |
| mastic | Mastic / silicone | joints |  |
| paumelle | Paumelle | articulation |  |
| pion_anti_degondage | Pion anti-dégondage | articulation |  |
| bras_pivot | Bras à souder / pivot | articulation |  |
| pivot_sol | Pivot de sol | articulation |  |
| serrure | Serrure | condamnation |  |
| kit_serrure | Kit serrure (coffre + gâche) | condamnation |  |
| coffre_serrure | Coffre de serrure | condamnation |  |
| gache | Gâche | condamnation |  |
| verrou | Verrou | condamnation |  |
| verrou_thermique | Verrou thermique | condamnation |  |
| cremone | Crémone | condamnation |  |
| pene | Pêne / tige | condamnation |  |
| ferme_porte | Ferme-porte | fermeture |  |
| selecteur_fermeture | Sélecteur de fermeture | fermeture |  |
| ouvre_porte | Ouvre-porte automatique | fermeture |  |
| barre_antipanique | Barre antipanique / push-bar | manoeuvre |  |
| bequille | Béquille / garniture / poignée | manoeuvre |  |
| taquet | Taquet d'entraînement | manoeuvre |  |
| gache_electrique | Gâche électrique / ouverture électrique | controle_acces |  |
| ventouse | Verrou électromagnétique en applique | controle_acces |  |
| passe_cable | Passe-câble | controle_acces |  |
| lecteur | Lecteur / clavier | controle_acces |  |
| contacteur | Contacteur de position | controle_acces |  |
| detecteur | Détecteur de sécurisation | controle_acces |  |
| cable | Câble de connexion | controle_acces |  |
| seuil_automatique | Seuil automatique | accessoire |  |
| busette | Busette / douille de drainage | accessoire |  |
| kit_protection | Kit / plaque de protection | accessoire |  |
| fixation | Fixation (vis, cheville, goujon) | fixation |  |
| cornière | Cornière / platine / étrier | fixation |  |
| calfeutrement | Calfeutrement (laine, compensateur) | calfeutrement |  |
| plaque_protection | Plaque de protection (plâtre, silicate) | calfeutrement |  |
| pare_vapeur | Pare-vapeur | calfeutrement |  |
| intercalaire | Intercalaire de vitrage isolant | remplissages |  |
| accessoire | Accessoire divers | accessoire |  |

## `ref_critere_feu`

| code | libelle | description |
|---|---|---|
| R | Capacité portante |  |
| E | Étanchéité au feu |  |
| I | Isolation thermique |  |
| I1 | Isolation thermique I1 |  |
| I2 | Isolation thermique I2 |  |
| W | Rayonnement |  |
| M | Action mécanique |  |
| C | Fermeture automatique |  |
| S | Étanchéité aux fumées |  |

## `ref_domaine_performance`

| code | libelle | description |
|---|---|---|
| feu | Résistance au feu |  |
| effraction | Résistance à l'effraction |  |
| balistique | Résistance aux balles |  |
| aev | Air - Eau - Vent |  |
| acoustique | Acoustique |  |

## `ref_fonction_serrure`

| code | libelle | description |
|---|---|---|
| W | Fonction W | Code fonction Forster tel qu'écrit dans les tableaux de serrures ; signification non définie dans le document |
| E | Fonction E | Code fonction Forster ; signification non définie dans le document |
| B | Fonction B | Code fonction Forster ; signification non définie dans le document |
| D | Fonction D | Code fonction Forster ; signification non définie dans le document |
| L+W | Fonction L+W | Code fonction Forster (serrure 2 points) ; signification non définie dans le document |

## `ref_grandeur`

| code | libelle | unite_code |
|---|---|---|
| largeur | Largeur | mm |
| hauteur | Hauteur | mm |
| surface | Surface | m2 |
| epaisseur | Épaisseur | mm |
| angle | Angle | deg |
| diametre | Diamètre | mm |
| longueur | Longueur | mm |
| jeu | Jeu | mm |
| pas | Pas / entraxe | mm |

## `ref_localisation`

| code | libelle | description |
|---|---|---|
| huisserie | Huisserie / dormant |  |
| vantail | Vantail (unique ou indifférent) |  |
| vantail_principal | Vantail principal |  |
| vantail_secondaire | Vantail secondaire / semi-fixe |  |
| cloison | Cloison / châssis |  |
| facade | Façade |  |
| support | Construction support |  |
| jonction | Jonction entre éléments |  |

## `ref_nature_valeur`

| code | libelle | description |
|---|---|---|
| teste | Valeur testée | Mesurée / observée lors d'un essai |
| autorise_max | Limite autorisée maximale | Domaine d'application (maximum) |
| autorise_min | Limite autorisée minimale | Domaine d'application (minimum) |
| autorise_exact | Valeur imposée | Valeur fixe imposée par le document |
| nominal | Caractéristique nominale de composant | Dimension / caractéristique de composant |
| exige_min | Exigence minimale | Exigence (ex. masse volumique support) |
| classement | Classement prononcé | Performance classée |

## `ref_objet_dimension`

| code | libelle | description |
|---|---|---|
| passage_libre | Passage libre |  |
| vantail_hors_tout | Vantail hors-tout |  |
| vitrage_hors_tout | Vitrage hors-tout |  |
| vitrage_clair | Clair de vitrage |  |
| vitrage_forme | Vitrage de forme |  |
| panneau | Panneau plein |  |
| cloison | Cloison vitrée |  |
| facade_entre_dalles | Façade : hauteur entre dalles |  |
| facade | Façade |  |
| imposte | Imposte |  |
| allege | Allège |  |
| ensemble | Ensemble (élément + imposte / cloison) |  |
| jeu_fonctionnement | Jeu de fonctionnement |  |
| empenage | Empênage |  |
| jeu_fond_feuillure | Jeu en fond de feuillure |  |
| prise_feuillure | Prise en feuillure |  |
| jeu_entre_vitrages | Jeu entre vitrages |  |
| film_adhesif | Film adhésif |  |
| plinthe | Plinthe |  |
| entraxe_traverses | Entraxe des traverses |  |
| angle_vitrages | Angle entre vitrages |  |
| chassis_facette | Châssis à facette |  |
| vantail_principal | Vantail principal |  |
| vantail_secondaire | Vantail secondaire |  |

## `ref_operateur`

| code | libelle |
|---|---|
| eq | égal à |
| le | inférieur ou égal à (maximum) |
| lt | strictement inférieur à |
| ge | supérieur ou égal à (minimum) |
| gt | strictement supérieur à |
| plage | plage min-max |

## `ref_role_composant`

| code | libelle | description |
|---|---|---|
| ossature_huisserie | Huisserie / bâti (dormant) |  |
| ossature_vantail | Cadre de vantail |  |
| traverse_basse_vantail | Traverse basse de vantail |  |
| traverse_intermediaire | Traverse intermédiaire |  |
| ossature_cloison | Ossature de cloison / façade |  |
| profile_rapporte | Profil rapporté |  |
| assemblage | Assemblage / manchonnage |  |
| remplissage | Élément de remplissage |  |
| maintien_remplissage | Maintien des remplissages |  |
| calage | Calage |  |
| etancheite | Étanchéité / joint |  |
| articulation | Articulation |  |
| condamnation | Condamnation / verrouillage |  |
| manoeuvre | Manœuvre |  |
| controle_acces | Contrôle d'accès |  |
| fermeture | Fermeture automatique |  |
| selecteur | Sélection de fermeture |  |
| accessoire | Accessoire complémentaire |  |
| fixation_support | Fixation à la construction support |  |
| calfeutrement | Calfeutrement |  |
| drainage | Drainage |  |
| jonction | Jonction / poteau |  |
| protection | Protection thermique d'un équipement |  |

## `ref_role_organisme`

| code | libelle | description |
|---|---|---|
| laboratoire | Laboratoire agréé émetteur |  |
| demandeur | Demandeur |  |
| co_demandeur | Co-demandeur / demandeur conjoint |  |
| fabricant_ossature | Fabricant / provenance de l'ossature |  |
| fabricant_vitrage | Fabricant / provenance des vitrages |  |
| laboratoire_essai | Laboratoire ayant réalisé un essai cité |  |

## `ref_statut_autorisation`

| code | libelle | description |
|---|---|---|
| autorise | Autorisé |  |
| obligatoire | Obligatoire |  |
| interdit | Interdit |  |
| remplace | Référence remplacée (par une extension) |  |
| remplacant | Référence de remplacement (autorisée par extension) |  |
| cite_essai | Cité dans un essai (pas une autorisation) |  |

## `ref_statut_extraction`

| code | libelle | description |
|---|---|---|
| extrait | Extrait du texte | Lecture directe fiable |
| ocr_degrade | OCR dégradé | Texte issu d'un scan, valeur plausible mais à relire |
| a_verifier | À vérifier | Ambiguïté d'attribution ou incohérence |
| non_trouve | Non trouvé | Information absente du corpus |

## `ref_statut_fiabilite`

| code | libelle | description |
|---|---|---|
| confirme | Confirmé (source fabricant officielle concordante) |  |
| a_verifier | À vérifier |  |

## `ref_type_articulation`

| code | libelle | description |
|---|---|---|
| paumelle | Paumelle |  |
| pion_anti_degondage | Pion anti-dégondage |  |
| bras_pivot | Bras à souder / pivot haut |  |
| pivot_sol | Pivot de sol |  |

## `ref_type_caracteristique`

| code | libelle | type_valeur | unite_code | description |
|---|---|---|---|---|
| section | Section (l x h ou l x e) | texte |  |  |
| largeur | Largeur | reel | mm |  |
| hauteur | Hauteur | reel | mm |  |
| epaisseur | Épaisseur | reel | mm |  |
| longueur | Longueur | reel | mm |  |
| diametre | Diamètre | reel | mm |  |
| materiau | Matériau | texte |  |  |
| marque | Marque / fabricant cité | texte |  |  |
| fonction | Fonction | texte |  |  |
| antipanique | Fonction antipanique | booleen |  |  |
| main | Main / sens DIN | texte |  |  |
| entraxe | Entraxe | reel | mm |  |
| nb_points | Nombre de points de fermeture | entier |  |  |
| longueur_plage | Plage de longueur | texte |  |  |
| force | Force de fermeture | texte |  |  |
| seuil_temperature | Seuil de déclenchement | reel | degC |  |
| position | Position de pose | texte |  |  |
| pas_pose | Pas de pose | reel | mm |  |
| reglable | Réglable | booleen |  |  |
| conditionnement | Conditionnement | texte |  |  |
| norme | Norme associée | texte |  |  |
| gamme | Gamme commerciale | texte |  |  |
| type | Type | texte |  |  |
| reversible | Réversible | booleen |  |  |
| compatibilite | Compatibilité (énoncée par la source) | texte |  |  |
| reaction_feu | Classement de réaction au feu | texte |  |  |
| masse_volumique | Masse volumique | reel | kg_m3 |  |

## `ref_type_controle`

| code | libelle | description |
|---|---|---|
| ocr_degrade | Texte OCR dégradé |  |
| planche_image | Planche image sans couche texte |  |
| incoherence | Incohérence interne ou inter-documents |  |
| non_trouve | Information non trouvée |  |
| document_absent | Document cité mais non fourni |  |
| ambiguite_attribution | Attribution de valeur ambiguë |  |

## `ref_type_document`

| code | libelle | description |
|---|---|---|
| pv_classement | Procès-verbal de classement | PV de classement de résistance au feu (arrêté du 22/03/2004 modifié) |
| reconduction | Reconduction | Prolonge la validité d'un PV et de ses extensions |
| extension | Extension de classement | Extension simple sur un PV |
| extension_multiple | Extension de classement multiple | Extension portant sur plusieurs PV |
| appreciation_laboratoire | Appréciation de laboratoire | Document de référence (non fourni) servant de base au PV |
| rapport_essai | Rapport d'essai | Rapport d'essai (non fourni sauf mention) |
| rapport_classement | Rapport de classement | Rapport de classement (EN 13501-2) |
| additif | Additif | Additif / modification |
| avis_chantier | Avis de chantier | Avis ponctuel du laboratoire |
| document_reference | Document de référence cité | Document cité, non présent dans le corpus |

## `ref_type_ferme_porte`

| code | libelle | description |
|---|---|---|
| applique | Ferme-porte en applique |  |
| encastre | Ferme-porte encastré |  |
| ouvre_porte | Ouvre-porte automatique |  |
| pivot_sol_frein | Pivot de sol à frein |  |
| selecteur | Sélecteur de fermeture |  |

## `ref_type_fixation`

| code | libelle | description |
|---|---|---|
| vis_beton | Vis béton (HUS…) |  |
| vis_cheville | Vis + cheville |  |
| goujon | Goujon d'ancrage |  |
| vis_metaux | Vis métaux |  |
| vis_tole | Vis à tôle / autoforeuse |  |
| rivet | Rivet |  |
| boulon | Boulon |  |
| soudure | Soudure |  |
| cheville_metal | Cheville métallique |  |

## `ref_type_joint`

| code | libelle | description |
|---|---|---|
| intumescent | Intumescent |  |
| epdm | EPDM |  |
| cr | CR (polychloroprène) |  |
| fibre_minerale | Bande de fibre minérale |  |
| fibre_ceramique | Bande de fibre céramique |  |
| butee | Joint de butée |  |

## `ref_type_relation`

| code | libelle | description |
|---|---|---|
| reconduit | reconduit | Source = reconduction ; cible = PV reconduit |
| reconduit_extension | reconduit l'extension | Source = reconduction ; cible = extension reconduite |
| non_reconduit | ne reconduit pas | Source = reconduction ; cible = extension explicitement non reconduite |
| etend | étend | Source = extension ; cible = PV de référence |
| remplace | annule et remplace | Source = nouvelle version ; cible = version remplacée |
| revise | révision de | Source = révision ; cible = indice précédent |
| a_pour_reference | a pour document de référence | Source = PV ; cible = rapport / appréciation de laboratoire |
| non_cumulable_avec | non cumulable avec | Interdiction explicite de cumul entre extensions |
| cumulable_avec | cumulable avec | Cumul explicitement autorisé |
| support_associe | montage dans élément classé par | Source = PV ; cible = PV de la construction support associée |
| annexe_de | annexe de | Document annexe |
| cite | cite | Simple citation |

## `ref_type_restriction`

| code | libelle | description |
|---|---|---|
| sens_feu | Sens du feu |  |
| cumul_extensions | Cumul / non-cumul d'extensions |  |
| interdiction | Interdiction |  |
| condition_mise_en_oeuvre | Condition de mise en œuvre |  |
| exclusion_normative | Exclusion (conformités non couvertes) |  |
| limitation_validite | Limitation de validité |  |
| condition_vitrage | Condition propre au vitrage |  |
| condition_combinaison | Condition de combinaison d'équipements |  |

## `ref_type_serrure`

| code | libelle | description |
|---|---|---|
| mortaiser | Serrure à mortaiser |  |
| solenoide | Serrure solénoïde |  |
| rouleau | Serrure à rouleau |  |
| commande_levier | Serrure de commande à levier (verrouillage automatique) |  |
| commande | Serrure de commande (verrouillage automatique) |  |
| cremone_levier | Crémone encastrée à levier |  |
| cremone_pompier | Crémone pompier |  |
| verrou_automatique | Verrou automatique à mortaiser |  |
| verrou_thermique | Verrou thermique |  |
| verrou_bascule | Verrou encastré levier à bascule |  |
| non_verrouille | Sans verrouillage |  |

## `ref_type_support`

| code | libelle | famille | description |
|---|---|---|---|
| beton_arme | Béton armé | rigide |  |
| beton_plein_parpaing | Béton plein / parpaings | rigide |  |
| beton_cellulaire | Béton cellulaire | rigide |  |
| maconnerie_beton_homogene | Blocs béton / maçonnerie / béton homogène | rigide |  |
| cloison_legere_98_48 | Cloison plaques de plâtre 98/48 | flexible |  |
| cloison_legere_120_70 | Cloison plaques de plâtre 120/70 | flexible |  |
| cloison_vitree_associee | Cloison vitrée classée (construction support associée) | associee |  |
| poteau_acier_protege | Poteau acier protégé | associee |  |
| dalle_beton | Dalle / voile béton armé | rigide |  |

## `ref_type_vitrage`

| code | libelle | description |
|---|---|---|
| monolithique | Monolithique |  |
| feuillete | Feuilleté |  |
| isolant | Isolant (double vitrage) |  |
| triple | Triple vitrage |  |
| isolant_store | Isolant à store intégré |  |
| angle_corner | Vitrage d'angle (corner) |  |
| isolant_angle | Isolant d'angle |  |

## `ref_type_zone_source`

| code | libelle | description |
|---|---|---|
| page_garde | Page de garde |  |
| texte | Texte courant |  |
| tableau | Tableau |  |
| planche | Planche / plan |  |
| note | Note |  |
| annexe | Annexe |  |
| suivi_revision | Suivi des révisions |  |

## `ref_typologie`

| code | libelle | description |
|---|---|---|
| bloc_porte | Bloc-porte |  |
| cloison_vitree | Cloison vitrée |  |
| cloison_vitree_bord_a_bord | Cloison vitrée à vitrages collés bord à bord |  |
| facade_vitree | Façade vitrée |  |
| chassis_fixe | Châssis fixe |  |

## `ref_unite`

| code | libelle | facteur_vers_si |
|---|---|---|
| mm | millimètre | 0.001 |
| m | mètre | 1.0 |
| m2 | mètre carré | 1.0 |
| deg | degré |  |
| kg_m3 | kilogramme par mètre cube | 1.0 |
| min | minute | 60.0 |
| um | micromètre | 1e-06 |
| degC | degré Celsius |  |
| kg | kilogramme | 1.0 |
| pa | pascal | 1.0 |
| db | décibel |  |
