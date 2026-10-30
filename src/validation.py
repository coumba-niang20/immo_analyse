import pandas as pd
from datetime import date
from nettoyage import cle_texte

# ---------- Seuils de plausibilité (modifiables) ----------
PRIX_MIN_ATYPIQUE = 100_000            # ventes
PRIX_MAX_ATYPIQUE = 2_000_000_000
LOYER_MIN_ATYPIQUE = 25_000            # locations (par mois)
LOYER_MAX_ATYPIQUE = 5_000_000
SURFACE_MIN_ATYPIQUE = 5
SURFACE_MAX_ATYPIQUE = 2000
CHAMBRES_MAX_APPART_STUDIO = 10

TYPES_VALIDES = {"Appartement", "Studio", "Chambre", "Villa", "Maison", "Terrain", "Local commercial"}
TRANSACTIONS_VALIDES = {"vente", "location"}
AUJOURDHUI = date.today().strftime("%Y-%m-%d")

# Lit le référentiel géographique. Renvoie les régions, les villes et les couples (région, ville) valides.
def charger_referentiel_geo(chemin="data/raw/referentiels/referentiel_geographique.csv"):
    ref = pd.read_csv(chemin, dtype=str)
    regions = {cle_texte(r): r for r in ref["region"].unique()}
    villes = {cle_texte(v): v for v in ref["ville"].unique()}
    couples = {(r, v) for r, v in zip(ref["region"], ref["ville"])}
    return regions, villes, couples

# Convertit un texte en entier. Renvoie None si ce n'est pas un nombre entier.
def _entier(texte):
    try:
        return int(float(texte))
    except ValueError:
        return None

# Contrôle une ligne. Renvoie les motifs de quarantaine et les avertissements.
def controler_ligne(ligne, couples):
    motifs = []
    avertissements = []
    est_location = ligne["type_transaction"] == "location"

    # ----- règles bloquantes (quarantaine) -----
    if ligne["id_local"].strip() == "":
        motifs.append("identifiant absent")
    if ligne["type_transaction"] not in TRANSACTIONS_VALIDES:
        motifs.append("type de transaction non interprétable")
    if pd.isna(ligne["prix_propre"]) or ligne["prix_propre"] <= 0:
        motifs.append("prix absent ou invalide")
    if pd.isna(ligne["surface_propre"]) or ligne["surface_propre"] <= 0:
        motifs.append("surface absente ou invalide")
    if pd.isna(ligne["date_propre"]):
        motifs.append("date impossible")
    elif ligne["date_propre"] > AUJOURDHUI:
        motifs.append("date future")
    if ligne["type_propre"] not in TYPES_VALIDES:
        motifs.append("type hors référentiel")
    if ligne["doublon_exact"]:
        motifs.append("doublon exact")

    # ----- avertissements (on garde la ligne) -----
    prix = ligne["prix_propre"]
    if not pd.isna(prix) and prix > 0:
        if est_location:
            if prix < LOYER_MIN_ATYPIQUE or prix > LOYER_MAX_ATYPIQUE:
                avertissements.append("loyer atypique")
        elif prix < PRIX_MIN_ATYPIQUE or prix > PRIX_MAX_ATYPIQUE:
            avertissements.append("prix atypique")
    if est_location and ligne["periodicite"] == "":
        avertissements.append("périodicité du loyer absente")
    surface = ligne["surface_propre"]
    if not pd.isna(surface) and surface > 0:
        if surface < SURFACE_MIN_ATYPIQUE or surface > SURFACE_MAX_ATYPIQUE:
            avertissements.append("surface atypique")
    if ligne["ville_propre"] == "":
        avertissements.append("ville absente")
    elif (ligne["region_propre"], ligne["ville_propre"]) not in couples:
        avertissements.append("région et ville incompatibles ou hors référentiel")

    chambres = _entier(ligne["chambres"])
    salles_bain = _entier(ligne["salles_bain"])
    if chambres is not None and chambres > CHAMBRES_MAX_APPART_STUDIO \
            and ligne["type_propre"] in ("Appartement", "Studio"):
        avertissements.append("nombre de chambres atypique")
    if chambres is not None and salles_bain is not None and salles_bain > chambres + 2:
        avertissements.append("salles de bain > chambres + 2")

    return pd.Series({"motifs": "; ".join(motifs), "avertissements": "; ".join(avertissements)})