# Interface et filtres (version 2 — charte Forster)

## Charte graphique
- Couleur principale : bleu Forster **#003C75** (Pantone 654C, relevé dans `L_Forster_rgb.svg`) ; teintes dérivées pour les fonds ; orange = « à vérifier », vert = « saisie relue », rouge = « échu ».
- Logo : `app/assets/logo-forster.svg` (bleu) et `logo-forster-blanc.svg` (en-tête sur fond bleu).
- Police : **Faktum** (Regular, Italic, Medium, SemiBold). **Les fichiers de police ne sont pas versionnés** : licence commerciale (René Bieder) et dépôt public. Les déposer dans `app/fonts/` (noms dans `app/fonts/LISEZMOI.txt`) sur le poste ou le serveur de diffusion ; sinon repli automatique sur Segoe UI / police système. Pour les servir sur GitHub Pages, il faut une licence web autorisant l'hébergement, ou un dépôt privé.

## Filtres disponibles
| Bloc | Filtre | Comportement |
|---|---|---|
| Recherche | Référence (avec auto-complétion sur les 1 773 références) | normalisée (espaces/points ignorés), alias inclus ; la carte affiche **où** la référence a été trouvée (document, planche/page, catégorie) |
| | Texte libre | sans accents, sur objets, composants, restrictions |
| Produit | Système Forster, Typologie, Verrier | puces multi-sélection **avec compteurs** recalculés selon les autres filtres ; options sans résultat grisées |
| | Nombre de vantaux | 1 / 2 (configuration saisie ou « Concernant » du PV) |
| Performance | Critère E / EW / EI + durée minimale | inclut les classements des extensions rattachées |
| | Classe lue dans le PV | exclut les classes reprises du nom de fichier (OCR illisible) |
| Vitrage | Gamme (compteurs) + type monolithique / feuilleté / isolant | |
| Quincaillerie | Catégorie de composant (compteurs), fonction de serrure, antipanique | |
| Dimensions | Passage libre / vantail / vitrage / hauteur d'ouvrage + largeur ≥, hauteur ≥ | largeur **et** hauteur dans un **même format** autorisé ; uniquement valeurs autorisées ; option « inclure les PV où la dimension n'a pas été extraite » (signalés sur la carte) |
| Mise en œuvre | Construction support (compteurs), allège autorisée | |
| Validité | Valide aujourd'hui (défaut) / échéance < 12 mois / échu / tous ; « valide au » | validité effective = dernière reconduction |
| | Type : PV de classement / PV DAS (CNPP) ; « uniquement saisis et relus » | |

Ergonomie : puces des filtres actifs retirables une à une, « Tout effacer », tri (numéro, validité, émission), **lien partageable** (filtres dans l'URL), **export CSV** de la sélection, fiche PV en onglets (Synthèse, Composants filtrables, Dimensions, Mise en œuvre, À vérifier) avec repère orange sur les lignes à vérifier, touche Échap pour fermer.

## Améliorations apportées par rapport à la v1
1. Facettes avec compteurs (on voit combien de PV restent avant de cliquer).
2. Dimensions rattachées à un objet précis (avant : n'importe quelle largeur du PV, y compris « largeur de cloison illimitée », faisait passer le filtre).
3. Largeur et hauteur vérifiées dans le même format (portrait/paysage).
4. Distinction classe lue / classe déduite du nom de fichier, et dédoublonnage.
5. État de validité par défaut « valide aujourd'hui », badges échu / échéance proche.
6. Explication du résultat pour la recherche par référence.
7. Performances : tables temporaires indexées (`rat`, `cls`) créées au chargement.

## Pistes suivantes (non réalisées)
- **Fonction de serrure / antipanique / main** sur tout le corpus : nécessite la relecture des tableaux de serrures (aujourd'hui seulement sur les PV saisis).
- **Compatibilité croisée porte ↔ cloison** : filtrer « bloc-porte intégrable dans la cloison X » via les relations `support_associe` (à compléter dans les PV automatiques).
- **Comparateur** de 2-3 PV côte à côte (classes, dimensions, supports, quincaillerie).
- **Filtre par épaisseur de vitrage** et par dimensions de vitrage : demande l'extraction des tableaux de vitrages.
- **Recherche par photo/plan** de planche : hors périmètre statique.
- **Alerte d'échéance** : liste des PV expirant dans l'année, exportable (déjà possible via État + export CSV).
