import json
import pandas as pd

# Colonnes communes : toutes les sources sont ramenées à ce même format.
COLONNES = ["source", "id_local", "date", "type_transaction", "type_bien", "region",
            "ville", "prix", "periodicite", "surface", "chambres", "salles_bain", "statut"]

# Garde seulement les colonnes communes, dans le même ordre (colonne absente = texte vide).
def _harmoniser(df):
    for colonne in COLONNES:
        if colonne not in df.columns:
            df[colonne] = ""
    return df[COLONNES]

# 1. import_historique.csv : CSV ";", encodage latin-1. Ce sont des ventes (colonne DateVente).
def charger_historique(chemin="data/raw/sources/import_historique.csv"):
    # keep_default_na=False : on garde "N/A" et les cases vides comme du texte
    df = pd.read_csv(chemin, sep=";", encoding="latin-1", dtype=str, keep_default_na=False)
    df["source"] = "import_historique"
    df = df.rename(columns={
        "ID": "id_local", "DateVente": "date", "Region": "region", "Ville": "ville",
        "TypeBien": "type_bien", "Prix": "prix", "Surface": "surface",
        "Chambres": "chambres", "SallesBain": "salles_bain",
    })
    df["type_transaction"] = "vente"
    return _harmoniser(df)

# 2. plateforme_immo_sn.csv : CSV ";", encodage UTF-8. Ventes et locations.
def charger_plateforme(chemin="data/raw/sources/plateforme_immo_sn.csv"):
    df = pd.read_csv(chemin, sep=";", encoding="utf-8", dtype=str, keep_default_na=False)
    df["source"] = "plateforme"
    df = df.rename(columns={
        "ref_plateforme": "id_local", "date_mise_en_ligne": "date", "categorie": "type_bien",
        "commune": "ville", "pieces": "chambres", "sdb": "salles_bain",
    })
    # périodicité : "FCFA/mois" = loyer mensuel ; "FCFA" seul = vente, donc pas de périodicité
    df["periodicite"] = df["devise"].apply(lambda d: "mensuel" if "mois" in d.lower() else "")
    return _harmoniser(df)

# 3. agence_teranga.xlsx : Excel, feuille "Annonces" (la feuille "Params" est ignorée).
def charger_agence(chemin="data/raw/sources/agence_teranga.xlsx"):
    df = pd.read_excel(chemin, sheet_name="Annonces", dtype=str, keep_default_na=False)
    df["source"] = "agence_teranga"
    df = df.rename(columns={
        "Code": "id_local", "Date": "date", "Region": "region", "Ville": "ville",
        "Type": "type_bien", "Prix_FCFA": "prix", "Surface_m2": "surface",
        "Chambres": "chambres", "SDB": "salles_bain", "Statut": "statut",
    })
    # pas de colonne de transaction : "Loué" et "Disponible" correspondent à des loyers
    # (même constat dans la plateforme), "En vente" et "Vendu" à des ventes
    df["type_transaction"] = df["statut"].apply(
        lambda s: "location" if s.strip().lower() in ("loué", "disponible") else "vente")
    return _harmoniser(df)

# 4. notaires.csv : CSV ",", encodage UTF-8. Actes de vente.
def charger_notaires(chemin="data/raw/sources/notaires.csv"):
    df = pd.read_csv(chemin, sep=",", encoding="utf-8", dtype=str, keep_default_na=False)
    df["source"] = "notaires"
    df = df.rename(columns={
        "id_acte": "id_local", "date_acte": "date", "montant_fcfa": "prix",
        "superficie": "surface", "nb_chambres": "chambres",
    })
    df["type_transaction"] = "vente"
    return _harmoniser(df)

# Convertit une valeur du JSON en texte ("" si absente), pour tout lire comme du texte.
def _en_texte(valeur):
    return "" if valeur is None else str(valeur)

# 5. particuliers.json : JSON imbriqué (annonce -> localisation, details). On l'aplatit.
def charger_particuliers(chemin="data/raw/sources/particuliers.json"):
    with open(chemin, encoding="utf-8") as f:
        donnees = json.load(f)
    lignes = []
    for element in donnees:
        annonce = element["annonce"]
        localisation = annonce.get("localisation", {})
        details = annonce.get("details", {})
        lignes.append({
            "source": "particuliers",
            "id_local": _en_texte(annonce.get("id")),
            "date": _en_texte(annonce.get("date")),
            "region": _en_texte(localisation.get("region")),
            "ville": _en_texte(localisation.get("ville")),
            "type_bien": _en_texte(details.get("type")),
            "type_transaction": _en_texte(details.get("transaction")),
            "prix": _en_texte(details.get("prix")),
            "surface": _en_texte(details.get("surface")),
            "chambres": _en_texte(details.get("chambres")),
            "salles_bain": _en_texte(details.get("sdb")),
            "statut": _en_texte(annonce.get("statut")),
        })
    return _harmoniser(pd.DataFrame(lignes))