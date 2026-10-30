import unicodedata
from datetime import datetime

# Nettoyage du prix : gère les espaces ("26 620 000"), "FCFA" et les millions ("57.62 millions").
# Renvoie None si impossible (ex. "N/A", "à négocier", "None FCFA") : on ne devine jamais un prix.
def nettoyer_prix(valeur):
    texte = valeur.strip().lower()
    texte = texte.replace("fcfa", "")            # "65575000 FCFA" -> "65575000"
    multiplicateur = 1
    if "million" in texte:                       # "57.62 millions" -> 57.62 x 1 000 000
        multiplicateur = 1_000_000
        texte = texte.replace("millions", "").replace("million", "")
    texte = texte.replace(" ", "")               # enlève les espaces : "26 620 000" -> "26620000"
    try:
        return round(float(texte) * multiplicateur)   # convertit en nombre
    except ValueError:
        return None                              # "N/A" ou "à négocier" ne peuvent pas devenir un nombre

# Remplace la virgule par un point et convertit en nombre. Renvoie None si impossible
# (ex. "quatre-vingt" : on ne convertit pas les nombres écrits en lettres).
def nettoyer_surface(valeur):
    texte = valeur.strip().replace(",", ".")      # "28,4" -> "28.4"
    try:
        return float(texte)
    except ValueError:
        return None

# Synonymes admis (referentiel_categories.csv) : variante en minuscules -> catégorie officielle.
SYNONYMES_TYPE = {
    "appart": "Appartement",
    "appt": "Appartement",
    "chambre simple": "Chambre",
    "local": "Local commercial",
    "bureau": "Local commercial",
    "magasin": "Local commercial",
    "terrains": "Terrain",
}

# Met en forme le type : minuscules, synonymes remplacés, première lettre en majuscule.
def nettoyer_type(valeur):
    texte = valeur.strip().lower()
    if texte in SYNONYMES_TYPE:
        return SYNONYMES_TYPE[texte]
    return texte.capitalize()

# Essaie plusieurs formats de date. Renvoie la date au format AAAA-MM-JJ, ou None si impossible.
def nettoyer_date(valeur):
    for format_date in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(valeur.strip(), format_date).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None

# Clé de comparaison : minuscules et sans accents ("GUÉDIAWAYE" -> "guediawaye").
def cle_texte(valeur):
    texte = unicodedata.normalize("NFD", valeur.strip().lower())
    return "".join(c for c in texte if unicodedata.category(c) != "Mn")

# Remplace une région ou une ville par son écriture officielle du référentiel.
# referentiel : dictionnaire {clé: nom officiel}. Si le nom est inconnu, on le garde tel quel.
def nettoyer_lieu(valeur, referentiel):
    return referentiel.get(cle_texte(valeur), valeur.strip())