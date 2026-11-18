# 16 — Rapports d'essais multi-domaines et cumuls de performances

Source : `Z:\FR-LIE\Forster-Technique\Rapports d'essais` (1 011 fichiers listés).

## 1. Périmètre retenu

| Dossier | Domaine (`ref_domaine_performance`) | PDF retenus |
|---|---|---|
| Résistance à l'effraction (RC) | `effraction` | rapports PfB, ift, CNPP, Buildwise/CSTC, PIV, GBD + synthèse Forster 16/05/2024 |
| Résistance aux balles (FB) | `balistique` | Beschussamt Ulm (FB4 à FB7), KADDB, certificats de vitrage |
| Résistance à l'explosion (EPR) | `explosion` | Fraunhofer EMI (EPR1 S / EPR1 NS) |
| A.E.V, Sismique, gradient thermique | `aev` | ift, GBD Lab, CEBTP, CSTB |
| Acoustique | `acoustique` | ift, GBD Lab, CEBTP, LaSM |
| Résistance aux chocs | `choc` | CSTB (M50), CEBTP (1200 J vitrages), ift (anti-pince-doigts) |
| Endurance / 1 Mo cycles / paumelles | `endurance` | ift, CSTB (EN 1191 / EN 12400 / EN 14024) |
| Portes issues de secours | `issue_secours` | ift (EN 179 / EN 1125) |
| Thermique | `thermique` | ift, CSTB (Uf, Uw) |
| Rapports de classement feu (EN 13501-2) | `feu` | ift, DMT |
| DTA Unico — rapports d'essais | `durabilite`, `aev`, `choc`… | CSTB, SGS, Institut de Soudure |
| Passeports CE | (document seul) | systèmes Forster |

Exclus : copies « Envois avec filigrane » (envois à des clients nommés), plans DWG/PDF, fiches de serrures, dossiers administratifs DTA, FDES/EPD, certificats matière, archives `.zip` (doublons des dossiers).
Résultat : **272 documents** (`DOC-RAP-*`), dont 225 rapports d'essais, 10 rapports de classement feu, 11 avis / expertises, 12 synthèses Forster, 6 certificats et 6 passeports CE. **259 performances** sont enregistrées.

## 2. Méthode (scripts/extract_rapports.py)

* Texte natif par page ; OCR fra+deu+eng uniquement sur les 6 premières et les 2 dernières pages sans texte.
* La classe vient du nom de fichier, ou du dossier (`RC1` / `RC2` / `RC3` / `RC4`), ou du texte (tableau de synthèse AEV, `Rw (C;Ctr) = …`). La page où elle est lue est conservée (`source_page`).
* Système, typologie, laboratoire, n° de rapport et date sont détectés automatiquement. Tout porte un `controle_humain` de type `extraction_auto`, plus `non_trouve` quand aucune classe n'a été lue (60 documents).
* Les rapports d'essais ne créent **aucune** performance feu. Seuls les 10 rapports de classement EN 13501-2 en créent (classes de la première page qui en contient).

## 3. Cumuls de performances — table `cumul_performance`

Un cumul n'est enregistré que s'il est **énoncé**, jamais déduit :

| statut_cumul | Signification | Nb |
|---|---|---|
| `declare_fabricant` | Synthèse Forster sans réserve (ex. fixes Unico RC2 + FB4) | 2 |
| `sous_reserve` | Synthèse Forster : « sous PV », « sur avis de chantier », serrures imposées | 17 |
| `constate_rapport` | Le même rapport porte deux classes (RC3 + FB4NS, RC4 + FB4) ou décrit l'éprouvette comme coupe-feu dans son nom (« PORTE EI30 », « CHASSIS FIXE EI30 ») | 40 |

### Ce qui est trouvé

* **Feu + effraction**
  * Fuego Light : portes EI30 RC2 (ift 15-001026-PR03 à PR09, PIV 45-28-21) et portes EI30 RC3 (ift 16-001854-PR01/03/04/05, PTE 04-08-1318).
  * Fuego Light : porte tôlée EI60 RC4 (GBD 15-0152-01) et fixes EI30 RC2/RC3 (16-001854-PR06/PR07).
  * Selon la synthèse Forster, uniquement « sous PV » ou « sur avis de chantier » : Unico E30 (portes RC2/RC3 avec PV Vetrotech EFR-22-001304), Presto 50/60S E30-E60, Thermfix Vario E30/E60/EI30/EI60 RC2-RC3, fenêtres Unico E30/60 RC2-RC3.
* **Feu + balistique** : Fuego Light EI30 FB4NS (portes 1 et 2 vantaux, châssis fixe — Beschussamt S11004201-B, S19020901B, S19020902B, S19022301B, S 21 0219 01Z).
* **Effraction + balistique** : Unico châssis fixes RC4 + FB4 (PfB 2012) et fenêtre + fixe RC3 + FB4NS (PfB 13-08-A288-G2) ; selon la synthèse Forster, fixes Unico RC2/RC3 + FB4.
* **Feu + acoustique** : Fuego Light portes EI30 / EI60 avec Rw mesuré (ift).
* Rien n'est énoncé pour : Unico RC4 + feu (« nous consulter » pour Thermfix Vario RC4), explosion (EPR1) + feu, Unico XS RC2 + feu.

### Règle d'interprétation

Un rapport d'effraction ou de balistique réalisé sur une porte « EI30 » ne vaut pas classement feu : le classement feu doit venir d'un PV couvrant **la même construction** (vitrage feu + contre-face P4A/P5A, serrure, ferme-porte, dimensions). La vue `v_cumul_potentiel` (et le filtre « Rapport d'essai disponible pour le même système et la même typologie » de l'application) ne fait qu'un rapprochement système × famille de typologie : c'est une piste à vérifier, pas un cumul.

## 4. Schéma (v1.3.0)

* `perf_explosion` (EPR1..4, S/NS) et `perf_mesure` (Uf, chocs, cycles, conformité EN 179/1125).
* `perf_effraction.classe_rc` accepte aussi WK1..WK6 (ancienne DIN V ENV 1627, voisine de RC sans être identique).
* `cumul_performance`, avec les vues `v_performance_multi` et `v_cumul_potentiel`.
* Nouveaux types de document : `avis_expertise`, `synthese_fabricant`, `passeport_ce`, `certificat`, `fiche_technique`.
* Nouvelles typologies : `porte_coulissante`, `composant`.
* Nouveaux systèmes : Omnia, Presto Norm, Presto (série non précisée).
* Requêtes : `Q21_cumuls_enonces`, `Q22_rapports_par_classe`, `Q23_croisement_potentiel_feu`.

## 5. Points de contrôle humains prioritaires

1. Rapports WK (2002-2009) dont le nom de fichier dit « RC » : classe d'origine à confirmer, ainsi que leur équivalence RC.
2. Rapport 08-10-A287-B1 : il est rangé dans le dossier RC2 mais cité en RC3 par la synthèse Forster.
3. AEV dont la classe vient du tableau de synthèse (statut `a_verifier`), et ceux sans classe lue.
4. Acoustique : plusieurs Rw par rapport (vitrage seul / ensemble) quand le nom de fichier ne précise pas la valeur retenue.
5. Rapports de 2025-2026 (GBD, CSTB, Thermfix Light CXL127-26) : laboratoire ou date non lus.
