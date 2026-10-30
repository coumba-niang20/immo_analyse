import pandas as pd
from validation import controler_ligne

COUPLES = {("Dakar", "Dakar"), ("Thiès", "Mbour")}

# Construit une ligne valide ; chaque test modifie seulement ce qu'il veut tester.
def ligne_valide(**changements):
    ligne = {
        "id_local": "A1", "type_transaction": "vente", "prix_propre": 50_000_000.0,
        "surface_propre": 100.0, "date_propre": "2020-01-01", "type_propre": "Maison",
        "doublon_exact": False, "periodicite": "", "ville_propre": "Dakar",
        "region_propre": "Dakar", "chambres": "3", "salles_bain": "2",
    }
    ligne.update(changements)
    return pd.Series(ligne)

def test_ligne_conforme_sans_motif_ni_avertissement():
    resultat = controler_ligne(ligne_valide(), COUPLES)
    assert resultat["motifs"] == ""
    assert resultat["avertissements"] == ""

def test_prix_absent_va_en_quarantaine():
    resultat = controler_ligne(ligne_valide(prix_propre=float("nan")), COUPLES)
    assert "prix absent ou invalide" in resultat["motifs"]

def test_prix_zero_va_en_quarantaine():
    resultat = controler_ligne(ligne_valide(prix_propre=0.0), COUPLES)
    assert "prix absent ou invalide" in resultat["motifs"]

def test_surface_negative_va_en_quarantaine():
    resultat = controler_ligne(ligne_valide(surface_propre=-30.0), COUPLES)
    assert "surface absente ou invalide" in resultat["motifs"]

def test_date_future_va_en_quarantaine():
    resultat = controler_ligne(ligne_valide(date_propre="2099-01-01"), COUPLES)
    assert "date future" in resultat["motifs"]

def test_doublon_exact_va_en_quarantaine():
    resultat = controler_ligne(ligne_valide(doublon_exact=True), COUPLES)
    assert "doublon exact" in resultat["motifs"]

def test_ville_absente_est_un_avertissement_pas_un_blocage():
    resultat = controler_ligne(ligne_valide(ville_propre=""), COUPLES)
    assert resultat["motifs"] == ""
    assert "ville absente" in resultat["avertissements"]

def test_surface_atypique_est_un_avertissement():
    resultat = controler_ligne(ligne_valide(surface_propre=3000.0), COUPLES)
    assert resultat["motifs"] == ""
    assert "surface atypique" in resultat["avertissements"]

def test_loyer_compare_aux_seuils_de_loyer():
    # 240 000 FCFA en location est normal, mais serait un prix de vente atypique
    location = controler_ligne(
        ligne_valide(type_transaction="location", prix_propre=240_000.0, periodicite="mensuel"), COUPLES)
    vente = controler_ligne(ligne_valide(prix_propre=50_000.0), COUPLES)
    assert location["avertissements"] == ""
    assert "prix atypique" in vente["avertissements"]

def test_location_sans_periodicite_est_signalee():
    resultat = controler_ligne(ligne_valide(type_transaction="location", prix_propre=240_000.0), COUPLES)
    assert "périodicité du loyer absente" in resultat["avertissements"]