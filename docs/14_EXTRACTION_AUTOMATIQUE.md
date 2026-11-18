# Extraction automatique du corpus complet (dossier « PV FEU Forster France E-EI / PV »)

Les 6 PV de départ ont été saisis et atomisés à la main (fichiers `data/sources/documents/<PV>.json`). Le reste du dossier réseau a été traité par une **chaîne automatique** pour que la base couvre tout le corpus immédiatement ; ses données sont **toutes marquées à vérifier**.

## Périmètre
- Traités : tous les PDF en cours du dossier (`FR …`), y compris les 6 procès-verbaux DAS du CNPP (`FR SA …`, type `pv_das`).
- Non traités : fichiers d'archive préfixés `ZZZ` (versions remplacées, « ne plus utiliser »), fichiers temporaires Word (`~$…`, `~WRL…`), `Thumbs.db`.
- Les 6 PV saisis à la main ne sont pas ré-extraits : la saisie manuelle prime toujours au build.

## Chaîne
1. `scripts/ocr_pdf.sh` : pour chaque page, texte natif (`pdftotext`) s'il existe, sinon OCR `tesseract -l fra` à 200 dpi. Une sortie `.txt` par PDF, pages séparées par `\f` (non versionnée : contenu intégral des PV).
2. `scripts/auto_extract.py <dossier_txt>` produit `data/sources/documents/AUTO-<n°>.json` (un par PDF), `AUTO-ZZ-CITES.json` (documents cités non fournis) et `data/sources/catalogue_auto.json` (nouvelles références, systèmes, organismes, normes, essais).
3. `scripts/build_db.py` fusionne : catalogue manuel puis automatique ; documents manuels puis automatiques ; un document « cité » dans un fichier et fourni dans un autre est remplacé par la version fournie ; les doublons de clé sont ignorés (première occurrence = manuelle).

## Ce qui est extrait automatiquement
| Donnée | Méthode | Fiabilité |
|---|---|---|
| Découpage du PDF en documents (reconductions, PV, extensions) | en-têtes « RECONDUCTION n° », « PROCÈS-VERBAL DE CLASSEMENT n° », « EXTENSION DE CLASSEMENT » + numéro de page 1 | bonne |
| Numéros, dates d'émission (« …, le 13 septembre 2022 ») et de validité (« jusqu'au : … ») | expressions régulières | bonne sur texte natif, moyenne en OCR |
| Relations : reconduit, extensions reconduites / non reconduites, étend, non cumulable | phrases types Efectis | bonne |
| Classements | tableau après « classé selon les combinaisons suivantes » ; complété par le nom de fichier si non lu (statut `non_trouve` + contrôle) | moyenne (tableaux OCR souvent illisibles) |
| Systèmes, vitrages (gamme + désignation), demandeurs | dictionnaires de motifs | bonne |
| Références de composants (Forster 9xxxxx, profilés NN.NNN, DORMA TS/ED/ITS/HZ/BTS/TV, STADI BS) | motifs + catégorie devinée par les mots voisins (paumelle, serrure, parclose…) | références fiables ; **catégorie indicative** |
| Dimensions « Hauteur / Largeur / Surface maximale … : N mm » | motif phrase | partielle ; les tableaux de dimensions de vitrages ne sont **pas** extraits |
| Sens du feu, « aucun autre classement », allège interdite, non-cumul | phrases types | bonne |
| Supports (béton armé, cellulaire, 98/48, 120/70) | mentions | indicative |

Non extrait automatiquement (à faire à la relecture) : attributs fins de serrures (fonction, main, antipanique, kit/coffre/gâche), paumelles 2D/3D, côté de pose des ferme-portes, tableaux de dimensions de vitrages, valeurs testées des essais, planches en image.

## Marquage
- Tous les documents automatiques : `statut_extraction = 'a_verifier'`, commentaire « Extraction automatique », un `controle_humain` de type `extraction_auto` indiquant les pages PDF concernées.
- Toutes les lignes dérivées (composants, dimensions, classements) : `a_verifier`, ou `non_trouve` pour une classe reprise du nom de fichier.
- `source_page.libelle` = « page PDF n » (pagination du fichier, pas celle du document).
- Dans l'application : badge « extraction automatique — à vérifier » et case « Uniquement les PV saisis et relus ».

## Limites connues
- Une extension multiple jointe à plusieurs PDF peut apparaître sous deux identifiants (ex. `EXT-MULT-EFR-22-002556` saisie à la main et `10-A-650/EXT-23/4` extraite) : à fusionner à la relecture.
- Les classements d'une extension multiple sont rattachés à l'extension, qui elle-même est rattachée à chaque PV visé : ils peuvent concerner un autre PV que celui affiché.
- Numéros d'extension lus en OCR : quelques erreurs possibles (contrôle `extraction_auto`).

## Promouvoir un PV automatique en saisie relue
1. Copier `AUTO-<n°>.json` vers `<n°>.json`, corriger / compléter (types `dc_*`, dimensions, pages réelles), passer les statuts à `extrait`.
2. Ajouter le n° à `manual_pvs` dans `scripts/auto_extract.py` (il ne sera plus ré-extrait) et supprimer le fichier `AUTO-`.
3. `build_db.py` → `test_queries.py` → commit.

## Résultat sur le dossier (18/11/2026)
| | |
|---|---|
| PDF traités automatiquement | 120 (5 261 pages, OCR tesseract fra) |
| Documents fournis (total base) | 346 : 112 PV de classement, 126 extensions (dont 13 multiples), 102 reconductions, 6 PV DAS CNPP |
| Documents cités non fournis | 119 |
| Occurrences de composants / références distinctes | 9 914 / 1 773 |
| Classements | 211 ; **72 PV** dont le tableau de classement n'a pas été lu par l'OCR → classe reprise du nom de fichier (`non_trouve`) |
| Contrôle de cohérence | validité effective calculée (dernière reconduction) = date du nom de fichier pour **112 / 112** PV |
