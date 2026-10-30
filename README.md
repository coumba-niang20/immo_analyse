# ImmoAnalyse

Pipeline Python qui charge des données immobilières hétérogènes (CSV, Excel, JSON),
les harmonise, les contrôle avec des règles métier explicites, met en quarantaine ce
qui n'est pas fiable et mesure la qualité des données.
Projet fil rouge du Module 1 : Python pour l'IA et le Machine Learning.

## Installation

    python3 -m venv .venv
    source .venv/bin/activate        # Windows : .venv\Scripts\activate
    pip install -r requirements.txt

## Exécution

    python src/main.py

Le programme lit les 5 sources dans data/raw/sources/ et le référentiel géographique
dans data/raw/referentiels/, puis écrit les résultats dans data/processed/,
data/quarantaine/ et reports/. Les données brutes ne sont jamais modifiées.

## Structure

- data/raw/            données brutes (sources/ et referentiels/), jamais modifiées
- data/processed/      donnees_propres.csv : lignes retenues
- data/quarantaine/    quarantaine.csv : lignes rejetées, avec la colonne motifs
- reports/             quality_report.json et quality_summary.csv
- docs/journal.md      décisions de nettoyage et justifications
- src/chargeurs.py     un chargeur par source, schéma commun de 13 colonnes
- src/nettoyage.py     fonctions de nettoyage (prix, surface, type, date, lieux)
- src/validation.py    seuils, règles métier et contrôle d'une ligne
- src/main.py          enchaîne chargement, nettoyage, contrôle, exports et rapport

## Sources traitées

| Source | Format | Lignes |
|---|---|---|
| import_historique.csv | CSV « ; », latin-1 | 528 |
| plateforme_immo_sn.csv | CSV « ; », UTF-8 | 875 |
| agence_teranga.xlsx | Excel (feuille Annonces) | 640 |
| notaires.csv | CSV « , », UTF-8 | 410 |
| particuliers.json | JSON imbriqué | 731 |

Colonnes communes : source, id_local, date, type_transaction, type_bien, region, ville,
prix, periodicite, surface, chambres, salles_bain, statut.

## Étapes du pipeline

1. Chargement : tout est lu en texte, sans que Pandas devine les valeurs manquantes.
2. Harmonisation : provenance (colonne source) et noms de colonnes communs.
3. Nettoyage : prix, surface, type de bien, date, région et ville.
4. Détection des doublons exacts.
5. Contrôle des règles métier : chaque ligne reçoit des motifs et des avertissements.
6. Séparation : données propres / quarantaine.
7. Rapport de qualité chiffré, global et par source.

## Règles appliquées

Bloquantes (la ligne va en quarantaine) :
identifiant absent, transaction non interprétable, prix absent ou <= 0,
surface absente ou <= 0, date impossible, date future,
type de bien hors des 7 catégories, doublon exact.

Avertissements (la ligne est conservée et signalée dans la colonne avertissements) :
prix atypique (ventes), loyer atypique (locations), périodicité du loyer absente,
surface atypique, ville absente, région et ville incompatibles,
plus de 10 chambres pour un appartement ou un studio, salles de bain > chambres + 2.

Normalisations : espaces, « FCFA » et « millions » dans les prix, virgule décimale
dans les surfaces, synonymes et casse des types de bien, dates JJ/MM/AAAA converties
en AAAA-MM-JJ, écriture des régions et villes alignée sur le référentiel.

Les seuils sont des constantes en haut de src/validation.py.
Les décisions et leurs justifications sont dans docs/journal.md.

## Fichiers produits

| Fichier | Contenu |
|---|---|
| data/processed/donnees_propres.csv | lignes retenues (colonne avertissements) |
| data/quarantaine/quarantaine.csv | lignes rejetées (colonne motifs) |
| reports/quality_report.json | indicateurs de qualité complets |
| reports/quality_summary.csv | conformité par règle |

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
Taux de conformité = conformes / évaluables (valeurs non vides).

## Décisions importantes

- Type de transaction : historique et notaires = vente. Pour l'agence, déduit du
  statut (Loué et Disponible = location), car les prix correspondent à des loyers.
- Un prix « à négocier » ou « N/A » n'est jamais deviné : la ligne va en quarantaine.
- Une ville vide est un avertissement, pas un blocage.
- Un loyer est comparé à des seuils de loyer, pas à ceux des ventes.
- Les surfaces écrites en lettres (« quatre-vingt ») ne sont pas converties.

## Limites

- Données synthétiques, non représentatives du marché réel.
- Les prix des ventes sont des prix demandés, pas des prix de transaction.
- Agence : 640 lignes lues, 680 annoncées dans la fiche de conception.
- Les doublons probables entre sources ne sont pas encore traités.
- Pas encore de tests unitaires ni de notebook d'analyse.
## Tests

    python -m pytest src -v

27 tests unitaires : cas conformes, invalides et limites.
