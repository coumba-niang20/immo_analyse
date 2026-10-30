
from nettoyage import (nettoyer_prix, nettoyer_surface, nettoyer_type,
                       nettoyer_date, nettoyer_lieu)

# ---------- nettoyer_prix ----------
def test_prix_conforme():
    assert nettoyer_prix("43758000") == 43758000

def test_prix_avec_espaces():
    assert nettoyer_prix("26 620 000") == 26620000

def test_prix_en_millions():
    assert nettoyer_prix("57.62 millions") == 57620000

def test_prix_avec_suffixe_fcfa():
    assert nettoyer_prix("65575000 FCFA") == 65575000

def test_prix_invalide_renvoie_none():
    assert nettoyer_prix("N/A") is None
    assert nettoyer_prix("à négocier") is None
    assert nettoyer_prix("") is None

# ---------- nettoyer_surface ----------
def test_surface_avec_point():
    assert nettoyer_surface("44.7") == 44.7

def test_surface_avec_virgule():
    assert nettoyer_surface("28,4") == 28.4

def test_surface_en_lettres_renvoie_none():
    assert nettoyer_surface("quatre-vingt") is None

def test_surface_negative_est_convertie_sans_etre_validee():
    # la conversion réussit ; c'est le contrôle (validation.py) qui rejette -30
    assert nettoyer_surface("-30") == -30.0

# ---------- nettoyer_type ----------
def test_type_casse():
    assert nettoyer_type("STUDIO") == "Studio"
    assert nettoyer_type("LOCAL COMMERCIAL") == "Local commercial"

def test_type_synonyme():
    assert nettoyer_type("appart") == "Appartement"
    assert nettoyer_type("bureau") == "Local commercial"

def test_type_espaces_autour():
    assert nettoyer_type("  Villa ") == "Villa"

# ---------- nettoyer_date ----------
def test_date_iso():
    assert nettoyer_date("2019-11-19") == "2019-11-19"

def test_date_jj_mm_aaaa():
    assert nettoyer_date("05/06/2018") == "2018-06-05"

def test_date_impossible_renvoie_none():
    assert nettoyer_date("32/13/2024") is None
    assert nettoyer_date("") is None

# ---------- nettoyer_lieu ----------
def test_lieu_casse_et_accents():
    referentiel = {"guediawaye": "Guédiawaye", "thies": "Thiès"}
    assert nettoyer_lieu("GUEDIAWAYE", referentiel) == "Guédiawaye"
    assert nettoyer_lieu("thies", referentiel) == "Thiès"

def test_lieu_inconnu_est_conserve():
    assert nettoyer_lieu("Dkr", {"dakar": "Dakar"}) == "Dkr"