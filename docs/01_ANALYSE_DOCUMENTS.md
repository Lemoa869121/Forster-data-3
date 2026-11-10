# 1-2. Analyse de la structure des documents joints

Corpus analysé : **6 fichiers PDF** du dossier Drive, contenant **17 documents logiques** (le nom de fichier ne désigne qu'un PV, mais la plupart des PDF sont des *compilations*). 21 autres documents sont **cités sans être fournis** (extensions manquantes, PV de constructions support, rapports et appréciations de référence) ; ils sont présents dans la base comme « documents de référence » (`present_dans_corpus = 0`) afin que toutes les relations restent exprimables.

## 1.1 Inventaire des fichiers

| Fichier (segment du nom) | Documents logiques dans le PDF (ordre) | Pages | Génération / qualité texte |
|---|---|---|---|
| `11-A-507 - VETR - porte PRESTO E30` | Reconduction 22/2 rév.1 → Reconduction 17/1 → **PV 11-A-507** (60 p.) → Ext. multiple EFR-14-000468 → Ext. 22/2 → Ext. multiple 23/4-23/3 | ~90 | PV 2012 scanné (OCR moyen, planches OCR très bruitées) ; pièces 2022-2023 natives |
| `13-A-175 - PYRO - cloison PRESTO E30` | Reconduction 23/2 → **PV 13-A-175** (26 p.) → Ext. multiple 14/1-14/2 | ~32 | PV 2013 OCR correct ; **extension 2014 scannée, OCR très dégradé** |
| `08-A-275 - PILK - cloison FUEGO light EI60` | Reconduction 24/3 → Reconduction 19/2 (avec *analyse* EN 1364-1:2015) → **PV 08-A-275** (35 p.) → Ext. 20/2 | ~43 | OCR correct ; planches partiellement lisibles |
| `13-A-704 - PILK - facade THERMFIX VARIO EI60` | Reconduction 24/2 → **PV 13-A-704** (51 p.) | 52 | OCR ; tableau des classements dégradé ; planches bilingues DE/FR/EN |
| `EFR-21-002687 - VETR - cloison vitrage bab FUEGO light EI30` | **PV EFR-21-002687** seul (45 p.) | 45 | PDF natif ; **35 planches en image sans texte** |
| `EFR-24-000553 - POLF - porte FUEGO Light EI30` | **PV EFR-24-000553 rév. 1** seul (77 p.) | 77 | PDF natif ; **65 planches en image sans texte** |

Le **nom de fichier** porte lui-même des métadonnées : numéro du PV, code fournisseur de vitrage (VETR, PYRO, PILK, POLF), typologie, système, classement principal, code marché (COPRO, PROFOR) et date de validité *effective* (celle de la dernière reconduction). Ces segments sont stockés dans `fichier_source` mais **ne remplacent jamais** la lecture du document (ex. « EI60 » dans le nom de 13-A-704 n'a servi qu'à corroborer un tableau OCR illisible, statut `ocr_degrade`).

## 1.2 Construction type d'un PV de classement (Efectis, arrêté du 22/03/2004 modifié)

| Section | Contenu | Où c'est stocké |
|---|---|---|
| Page de garde | N° PV, révision, date de validité, rapport/appréciation de référence, « Concernant » (objet, ossature, vitrages), demandeurs | `document`, `document_organisme`, `document_relation(a_pour_reference)` |
| Suivi des révisions (PV récents) | Indice, modification, date, rédacteur / vérificateur / approbateur | `document_relation(remplace)`, `document_signataire` |
| §1 / §2 Description sommaire, référence et provenance | Système, usines de production ossature et vitrages | `document_systeme`, `document_organisme(fabricant_*)` |
| §1.2.x / §3.3.x Description détaillée | Huisserie, vantail, profilés **par rôle**, vitrages et variantes, panneaux, maintien (parcloses, joints, cales), **quincaillerie** (articulation, verrouillage, manœuvre, contrôle d'accès, fermeture, sélecteurs, pivots, accessoires), jeux, jonctions/poteaux, constructions support | `document_composant` + tables typées `dc_*`, `support_pose`, `dimension_format` |
| §3 / §5 Classement | Référence normative (EN 13501-2 + §7.5.x), tableau R E I W t M C S G K, « Aucun autre classement n'est autorisé » | `performance` + `perf_feu`, `document_norme`, `restriction` |
| §4 / §6 Conditions de validité | Fabrication/mise en œuvre, **sens du feu**, **domaine de validité** (dimensions max/min, surfaces, formes) | `restriction(sens_feu)`, `dimension_format` / `dimension` |
| §5 / §7 Durée de validité | 5 ans, date en toutes lettres | `document.date_validite` |
| Exclusions (PV 2024) | Conformités non couvertes : SVE, DAS, contrôle d'accès (EN 1125, EN 179, NF S 61-937…) | `restriction(exclusion_normative)`, `document_norme(role='exclusion')` |
| Annexe planches | Coupes, profilés, **tableaux de références** (serrures, parcloses/joints par épaisseur de vitrage, compositions de vitrages), fixations | `document_composant` avec `source_page.planche`, sinon `controle_humain(planche_image)` |

**Reconduction** (1–2 p.) : PV reconduit, extensions reconduites (et parfois *non* reconduites : 18/1 sur 08-A-275), nouvelle date de validité, parfois une *analyse* technique (19/2 : thermocouples DIN vs EN 1364-1:2015).
**Extension** (3–15 p.) : objet, PV visé(s) (une extension *multiple* vise plusieurs PV), §1 modifications, §2 justification par essais cités (avec **durées mesurées** = valeurs testées), §3 conditions (nouvelles dimensions), §4 conclusions + règle de **cumul**.

## 1.3 Informations réparties ou implicites

- **Validité effective** : la date d'un PV ancien (2014, 2017, 2018) n'est plus la bonne ; seule la dernière reconduction fait foi → vue `v_validite_effective`.
- **Validité des extensions** : « celle du PV de référence » → `document.validite_liee_au_pv = 1`, pas de date propre.
- **Références de serrures** : dans le texte, seulement des *types* (« serrure à mortaiser 2 points ») ; les références exactes, fonctions (W, E, B, D, L+W), main DIN, antipanique et associations kit/coffre/gâche sont **dans des tableaux de planches** (11-A-507 pl. 30 et 33) ou **en image** (EFR-24-000553 pl. 48).
- **Dimensions de vitrage** : souvent plusieurs formats alternatifs (« OU ») portrait/paysage, parfois avec surface max → `dimension_format.groupe_alternative`.
- **Clair de vitrage vs hors-tout** : 13-A-175 et 08-A-275 donnent des *clairs*, les autres du *hors-tout* → `objet_code` distinct (`vitrage_clair` / `vitrage_hors_tout`), jamais comparés directement.
- **Conditions de combinaison** : « semi-fixe sans verrouillage si et seulement si le principal a une serrure 2 points » ; « seuil STADI BS uniquement avec 32.855/32.854 » → `restriction(condition_combinaison)`.
- **Références remplacées** : 917611 (anciennement 907642) ; HZ33F → HZ43F par extension → `reference_alias`, `statut_autorisation_code = remplace / remplacant`.
- **Valeurs testées** : n'apparaissent que dans les justifications d'extensions (ex. EFR-21-002096-B : E 31 min, W 14 min) → `essai_resultat` (nature `teste` imposée par CHECK).

## 2. Points communs et différences

| Aspect | PV « génération 2008-2013 » (08-A-275, 11-A-507, 13-A-175, 13-A-704) | PV « génération 2022-2024 » (EFR-21-002687, EFR-24-000553) |
|---|---|---|
| Référentiel | Arrêté du 22/03/2004 ; EN 13501-2 (2004/2007 ou non daté) | Arrêté du 14/03/2011 modifiant 2004 ; EN 13501-2:2016 / 2023 |
| Numérotation | `AA-A-NNN` ; extensions `AA/N` ; reconductions `AA/N` | `EFR-AA-NNNNNN` ; révisions indicées |
| Document de référence | « Rapport de référence » | « Appréciation de laboratoire de référence » |
| Validité | Prolongée par reconductions successives (2 à 3) | Validité initiale en cours |
| Texte | Scans OCR (bruit, inversions de colonnes, « E160 » pour « EI 60 ») | Texte natif propre |
| Planches | Texte OCR partiel (tableaux de références exploitables avec relecture) | **Images pures** : rien d'extractible automatiquement |
| Exclusions normatives | Absentes | Présentes (SVE, DAS, contrôle d'accès) |
| Classement | E 30 / EW 30 / EI 60 … | ajoute **I2** (EI2 30 bloc-porte) |

Différences de **typologie** : bloc-porte (11-A-507, EFR-24-000553) → riche en quincaillerie et passages libres ; cloison vitrée (13-A-175, 08-A-275, EFR-21-002687) → vitrages, hauteurs, supports ; façade (13-A-704) → profilés de dimensionnement statique, fixations nez de dalle, calfeutrements, et des **mesures RC2/RC3** (effraction) présentées en planches *sans classement effraction prononcé* — ce n'est donc pas une performance.

Différences de **logique de vitrage** : un même PV peut prononcer des classements différents selon la famille de vitrage (13-A-175 : E 30 avec PYROGUARD E30, EW 30 avec PYROGUARD EW30) → une `configuration` par famille, jamais fusionnées.

## 2.1 Incohérences et ambiguïtés relevées (toutes tracées dans `controle_humain`)

- Ext. 23/4-23/3 : numéro « 23/4 » en page de garde, « 23/3 » en en-tête pour 11-A-507.
- 13-A-175 : béton cellulaire « > 500 » (§1.2.4.1) vs « > 550 kg/m³ » (§4.3.1).
- 08-A-275 ext. 20/2 : dimensions « du PV de référence » (1540 x 2495) ≠ PV fourni (1516 x 2471).
- 11-A-507 : ferme-porte lu « 1593 (DORMA) » vs planche 42 « kit 904001 au TS93 uniquement ».
- EFR-21-002687 : profils 736.83x présentés « Fuego Light 30 » alors que 736.xxx = Fuego Light 60 ailleurs ; jeu Palusol 3 mm vs 4 mm.
- EFR-24-000553 vs 11-A-507 ext. 22/2 : verrous thermiques / serrure à rouleau proches mais **cotes différentes** (1262 vs 1282 mm ; Ø25 vs Ø26) → deux variantes distinctes.
- Extensions citées mais absentes : 18/1 (08-A-275), 18/2 (13-A-175), 18/1 (13-A-704).

Liste complète et à jour : [`13b_CONTROLES_OUVERTS.md`](13b_CONTROLES_OUVERTS.md).
