# Journal de décisions : ImmoAnalyse

## Étape A : chargement de import_historique.csv
- **Quoi** : lecture avec `sep=";"`, `encoding="latin-1"`, `dtype=str`, `keep_default_na=False`.
- **Pourquoi** : le fichier est en latin-1 (accents cassés sinon). Tout est lu en texte pour ne pas laisser Pandas deviner : `N/A` et `37 965 000` restent visibles.
- **Décision** : `keep_default_na=False`. Sans cela, Pandas transforme `N/A` et les cases vides en valeurs manquantes (`NaN`) et le nettoyage plante. Une case vide devient un texte vide `""`.
- **Résultat chiffré** : 528 lignes, 9 colonnes.
- **Limites** : aucune.

## Étape B : provenance et noms de colonnes
- **Quoi** : colonne `source = "import_historique"`, colonnes renommées (ID → id_local, Prix → prix, etc.).
- **Pourquoi** : tracer l'origine de chaque ligne et préparer la fusion avec les autres sources.
- **Résultat chiffré** : 9 colonnes renommées.
- **Limites** : le fichier n'a pas de colonne type_transaction.

## Étape C : nettoyage du prix
- **Quoi** : suppression des espaces, conversion en nombre. Les valeurs impossibles (`N/A`) deviennent vides.
- **Pourquoi** : règle « normalisable » pour les espaces ; « bloquante » pour un prix absent.
- **Résultat chiffré** : 72 prix avec espaces corrigés, 10 prix impossibles (`N/A`).
- **Décision** : `N/A` est une erreur de conversion (la cellule n'est pas vide, mais ce n'est pas un nombre). Ces lignes iront en quarantaine.
- **Limites** : on ne devine jamais un prix manquant.

## Étape D : nettoyage de la surface
- **Quoi** : remplacement de la virgule décimale par un point, puis conversion en nombre.
- **Pourquoi** : règle « normalisable » (virgule décimale dans les surfaces).
- **Résultat chiffré** : 50 virgules corrigées, 0 surface impossible.
- **Limites** : la plausibilité de la surface (trop petite ou trop grande) est vérifiée à l'étape G.

## Étape E : normalisation du type de bien
- **Quoi** : suppression des espaces autour, première lettre en majuscule, reste en minuscule.
- **Pourquoi** : règle « normalisable » (casse). Sans cela, STUDIO et Studio seraient deux types.
- **Résultat chiffré** : 14 variantes ramenées à 7 types (Local commercial 88, Maison 82, Appartement 79, Chambre 73, Terrain 71, Villa 71, Studio 64, soit 528).
- **Limites** : aucun synonyme dans ce fichier ; à gérer pour les autres sources.

## Étape F : normalisation des dates
- **Quoi** : conversion des formats AAAA-MM-JJ et JJ/MM/AAAA vers AAAA-MM-JJ.
- **Pourquoi** : règle « normalisable » (dates JJ/MM/AAAA ou ISO).
- **Décision d'ambiguïté** : les dates avec « / » sont lues en jour/mois, car certaines (16/10/2018, 25/12/2019) ne peuvent pas être mois/jour.
- **Résultat chiffré** : 215 dates converties, 0 impossible, 0 future.
- **Limites** : la décision repose sur le reste du fichier.

## Étape G : contrôle des règles et quarantaine
- **Quoi** : chaque ligne reçoit deux colonnes : `motifs` (règles bloquantes violées) et `avertissements` (anomalies tolérées). Plusieurs problèmes sont séparés par « ; ».
- **Pourquoi** : règles de regles_metier.md. Les seuils (prix, surface) sont des constantes en haut du fichier, pas du code en dur.
- **Règles bloquantes** : identifiant absent, prix absent ou ≤ 0, surface absente ou ≤ 0, date impossible, date future, type hors des 7 catégories.
- **Avertissements** : prix atypique, surface atypique, ville absente.
- **Résultat chiffré** : 10 lignes en quarantaine (prix `N/A`), 518 retenues, dont 8 avec avertissement (ville absente).
- **Décision** : une ville vide est un avertissement, pas un blocage : la région est connue et on ne devine jamais la ville. Aucune date future, aucun doublon exact.
- **Limites** : pas encore de contrôle des chambres et salles de bain, ni de cohérence région/ville.

## Étape H : stockage des résultats
- **Quoi** : les lignes sans motif vont dans `data/processed/donnees_propres.csv` ; les lignes avec motif vont dans `data/quarantaine/quarantaine.csv`.
- **Pourquoi** : les données brutes restent intactes dans `data/raw/`, chaque rejet a sa justification (colonne `motifs`), et les avertissements restent visibles dans les données propres.
- **Résultat chiffré** : 518 lignes propres (510 normales + 8 avec avertissement), 10 en quarantaine, soit 528 au total : aucune ligne perdue.
- **Décision** : une ligne avec avertissement n'est pas mise en quarantaine, car elle est exploitable. On la garde avec son signalement.
- **Limites** : les lignes en quarantaine ne sont pas corrigées ; elles devront être revues à la source.

## Étape I : rapport de qualité
- **Quoi** : indicateurs exportés dans `reports/quality_report.json` et `reports/quality_summary.csv`.
- **Définitions** : taux de conformité = conformes / évaluables. Les valeurs non évaluables sont comptées à part, jamais considérées comme conformes. « Entièrement conforme » = ni motif ni avertissement.
- **Résultat chiffré** : 528 reçues, 358 corrigées, 510 entièrement conformes. Conformité : prix 98,11 %, toutes les autres règles 100 %.
- **Décision** : `N/A` dans le prix est une erreur de conversion (la cellule n'est pas vide), pas une valeur manquante.
- **Limites** : une seule source traitée sur 5.

## Décisions prises hors règles écrites (à valider avec le formateur)
- **Ville vide** : avertissement, pas quarantaine. Les règles ne parlent que de villes incompatibles avec la région. Ici la région est connue et la ligne reste exploitable.
- **Type hors référentiel** : quarantaine. Le cahier des charges dit « quarantaine », `regles_metier.md` dit « signaler ». J'applique le cahier des charges. Sans effet sur import_historique (7 types valides), à trancher pour les autres sources.
- **Doublon exact** : mêmes valeurs sur toutes les colonnes sauf l'identifiant, car les identifiants ne sont pas fiables.
- **Ligne corrigée** : au moins une normalisation appliquée (espace dans le prix, virgule dans la surface, date en JJ/MM/AAAA ou casse du type changée). 358 lignes.
## Sources traitées

| Source | Format | Lignes |
|---|---|---|
| import_historique.csv | CSV « ; », latin-1 | 528 |
| plateforme_immo_sn.csv | CSV « ; », UTF-8 | 875 |
| agence_teranga.xlsx | Excel (feuille Annonces) | 640 |
| notaires.csv | CSV « , », UTF-8 | 410 |
| particuliers.json | JSON imbriqué | 731 |

## Résultats (3184 enregistrements)

| Source | Propres | Quarantaine | Propres avec avertissement |
|---|---|---|---|
| agence_teranga | 631 | 9 | 126 |
| import_historique | 518 | 10 | 69 |
| notaires | 390 | 20 | 0 |
| particuliers | 595 | 136 | 199 |
| plateforme | 845 | 30 | 36 |
| **Total** | **2979** | **205** | **430** |

Entièrement conformes : 2549. Corrigées : 1222. Doublons exacts : 15.
Conformité : prix 99,26 %, surface 99,74 %, date 99,65 %, autres règles 100 %.
## Étape M : tests unitaires
- **Quoi** : 27 tests (pytest) sur les fonctions de nettoyage et sur le contrôle des règles : cas conformes, invalides et limites (prix à 0, surface négative, date future, loyer contre prix de vente).
- **Pourquoi** : la validation du projet ne doit pas reposer sur l'absence d'erreur à l'exécution.
- **Résultat chiffré** : 27 passés, 0 échec.
- **Lancement** : `python -m pytest src -v`.