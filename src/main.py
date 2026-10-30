import json
import os
import pandas as pd

from chargeurs import (charger_historique, charger_plateforme, charger_agence,
                       charger_notaires, charger_particuliers, COLONNES)
from nettoyage import (nettoyer_prix, nettoyer_surface, nettoyer_type,
                       nettoyer_date, nettoyer_lieu)
from validation import (charger_referentiel_geo, controler_ligne,
                        TYPES_VALIDES, TRANSACTIONS_VALIDES, AUJOURDHUI)

# ---------- 1. Chargement des 5 sources et empilement ----------
df = pd.concat([
    charger_historique(), charger_plateforme(), charger_agence(),
    charger_notaires(), charger_particuliers(),
], ignore_index=True)

# ---------- 2. Nettoyage ----------
regions, villes, couples = charger_referentiel_geo()

df["prix_propre"] = df["prix"].apply(nettoyer_prix)
df["surface_propre"] = df["surface"].apply(nettoyer_surface)
df["type_propre"] = df["type_bien"].apply(nettoyer_type)
df["date_propre"] = df["date"].apply(nettoyer_date)
df["region_propre"] = df["region"].apply(lambda v: nettoyer_lieu(v, regions))
df["ville_propre"] = df["ville"].apply(lambda v: nettoyer_lieu(v, villes))
df["type_transaction"] = df["type_transaction"].str.strip().str.lower()

# doublon exact : ligne identique à une ligne précédente (même source, même identifiant, mêmes valeurs)
df["doublon_exact"] = df.duplicated(subset=COLONNES, keep="first")

# ---------- 3. Contrôle des règles métier ----------
df[["motifs", "avertissements"]] = df.apply(lambda ligne: controler_ligne(ligne, couples), axis=1)

# ---------- 4. Séparation et exports ----------
quarantaine = df[df["motifs"] != ""]
propres = df[df["motifs"] == ""]

os.makedirs("data/processed", exist_ok=True)
os.makedirs("data/quarantaine", exist_ok=True)
os.makedirs("reports", exist_ok=True)

quarantaine.to_csv("data/quarantaine/quarantaine.csv", index=False)
propres.to_csv("data/processed/donnees_propres.csv", index=False)

# ---------- 5. Rapport de qualité ----------
cols_brutes = ["id_local", "date", "region", "ville", "type_bien", "prix", "surface", "chambres", "salles_bain"]

# valeurs manquantes par colonne (cellule vide dans le fichier d'origine)
manquants = {c: int((df[c].str.strip() == "").sum()) for c in cols_brutes}

# erreurs de conversion : valeur présente mais non convertible
erreurs_conversion = {
    "prix": int((df["prix_propre"].isna() & (df["prix"].str.strip() != "")).sum()),
    "surface": int((df["surface_propre"].isna() & (df["surface"].str.strip() != "")).sum()),
    "date": int((df["date_propre"].isna() & (df["date"].str.strip() != "")).sum()),
}

# lignes corrigées : au moins une normalisation appliquée
corrigee = (
    df["prix"].str.contains(" ") | df["prix"].str.lower().str.contains("million|fcfa")
    | df["surface"].str.contains(",")
    | df["date"].str.contains("/")
    | (df["type_bien"].str.strip() != df["type_propre"])
    | (df["region"].str.strip() != df["region_propre"])
    | (df["ville"].str.strip() != df["ville_propre"])
)

# conformité par règle : conformes / évaluables
regles = {
    "identifiant présent": ("id_local", df["id_local"].str.strip() != ""),
    "transaction valide": ("type_transaction", df["type_transaction"].isin(TRANSACTIONS_VALIDES)),
    "prix valide": ("prix", df["prix_propre"] > 0),
    "surface valide": ("surface", df["surface_propre"] > 0),
    "date valide et non future": ("date", df["date_propre"].notna() & (df["date_propre"].fillna("") <= AUJOURDHUI)),
    "type dans le référentiel": ("type_bien", df["type_propre"].isin(TYPES_VALIDES)),
}

lignes_regles = []
for nom, (colonne, ok) in regles.items():
    evaluables = df[colonne].str.strip() != ""
    n_eval = int(evaluables.sum())
    n_conf = int((ok & evaluables).sum())
    lignes_regles.append({
        "regle": nom,
        "evaluables": n_eval,
        "non_evaluables": len(df) - n_eval,
        "conformes": n_conf,
        "non_conformes": n_eval - n_conf,
        "taux_conformite_pct": round(n_conf / n_eval * 100, 2),
    })

# bilan par source
par_source = []
for source, groupe in df.groupby("source"):
    par_source.append({
        "source": source,
        "recus": len(groupe),
        "propres": int((groupe["motifs"] == "").sum()),
        "quarantaine": int((groupe["motifs"] != "").sum()),
        "avec_avertissement": int(((groupe["motifs"] == "") & (groupe["avertissements"] != "")).sum()),
    })

nb_doublons = int(df["doublon_exact"].sum())
rapport = {
    "enregistrements_recus": len(df),
    "valeurs_manquantes_par_colonne": manquants,
    "doublons_exacts": nb_doublons,
    "taux_doublons_pct": round(nb_doublons / len(df) * 100, 2),
    "erreurs_conversion_par_champ": erreurs_conversion,
    "enregistrements_corriges": int(corrigee.sum()),
    "enregistrements_en_quarantaine": len(quarantaine),
    "enregistrements_conserves_avec_avertissement": int((propres["avertissements"] != "").sum()),
    "enregistrements_entierement_conformes": int(((df["motifs"] == "") & (df["avertissements"] == "")).sum()),
    "par_source": par_source,
    "regles": lignes_regles,
}

with open("reports/quality_report.json", "w", encoding="utf-8") as f:
    json.dump(rapport, f, ensure_ascii=False, indent=2)

pd.DataFrame(lignes_regles).to_csv("reports/quality_summary.csv", index=False)

print("Reçues :", len(df))
print("Propres :", len(propres))
print("Quarantaine :", len(quarantaine))
print("Avec avertissement :", (propres["avertissements"] != "").sum())
print(pd.DataFrame(par_source).to_string(index=False))
print("Motifs de quarantaine :")
print(quarantaine["motifs"].str.split("; ").explode().value_counts().to_string())
print("Avertissements :")
print(propres["avertissements"].str.split("; ").explode().replace("", pd.NA).dropna().value_counts().to_string())
print(pd.DataFrame(lignes_regles)[["regle", "evaluables", "conformes", "taux_conformite_pct"]].to_string(index=False))
print("Corrigées :", int(corrigee.sum()), "| Entièrement conformes :", rapport["enregistrements_entierement_conformes"], "| Doublons exacts :", nb_doublons)