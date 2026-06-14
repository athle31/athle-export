#!/usr/bin/env python
import argparse
import os
import pandas as pd

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)

def main_bemi(dataframe):
    def total_indiv(df):
        df["calcul"] = " / ".join([f"{a} ({b})" for a, b in zip(df["points"].values,
                                                                df["competition"].values)]) 
        df["points"] = sum(df["points"].nlargest(2))
        return df

    def total_club(df):
        garcons = df.loc[df["sexe"]=="M"].nlargest(2, "points")
        filles = df.loc[df["sexe"]=="F"].nlargest(2, "points")
        df["membres"] = ", ".join(filles["nom/prenom"].values.tolist()\
                                 +garcons["nom/prenom"].values.tolist())
        
        df["points"] = sum(df.loc[df["sexe"]=="M", "points"].nlargest(2)) \
            + sum(df.loc[df["sexe"]=="F", "points"].nlargest(2))
        return df

    dataframe = dataframe[dataframe["epreuve"].str.startswith("Triathlon")]
    dataframe = dataframe[dataframe["departement"]==31]
    dataframe = dataframe[~(dataframe["nom/prenom"] == "Identité non communiquée")]

    dataframe = dataframe.copy()
    dataframe["club"] = dataframe["club"].apply(
        lambda x: x.split(" - S/l")[0] if "S/l" in x else x)
    dataframe["points"] = pd.to_numeric(dataframe["performance"].str.replace(" pts", ""))
    dataframe = dataframe.groupby("id",
                                  group_keys=True).apply(total_indiv).reset_index(drop=True)
    dataframe.drop(columns=["Unnamed: 0", "place", "vent", "competition", "performance", "niveau"], inplace=True)
    dataframe.drop_duplicates(inplace=True)
    dataframe = dataframe.sort_values(by="points", ascending=False)
    indiv = dataframe.copy()
    indiv = indiv.loc[:, ["nom/prenom","club","points", "calcul", "categorie", "departement", "region" , "epreuve"]]

    dataframe["sexe"] = dataframe["categorie"].str[2]
    dataframe["unisexe"] = dataframe["categorie"].str[:2] + "X"
    dataframe["unisexe.keep"] = dataframe["unisexe"]
    dataframe["club.keep"] = dataframe["club"]
    dataframe = dataframe.groupby(["club", "unisexe"],
                                  group_keys=True).apply(total_club).reset_index(drop=True) 
    dataframe = dataframe.sort_values(by="points", ascending=False)
    dataframe.drop(columns=["calcul", "sexe", "categorie", "nom/prenom"], inplace=True)
    dataframe.drop_duplicates(inplace=True)
    equipes = dataframe.copy()
    equipes = equipes.rename(columns={"unisexe.keep": "categorie"})
    equipes["club"] = equipes["club.keep"]

    equipes = equipes.loc[:, ["club", "points", "categorie", "membres", "departement", "region", "epreuve"]]

    return indiv, equipes


def main_caju(dataframe):
    famille = dict()
    famille["sprint/haies"] = ["100m", "200m", "400m", "Haies"]
    famille["demifond"] = ["800m", "1 500m", "000m"]
    famille["marche"] = ["Marche"]
    famille["sauts"] = ["Perche", "Longueur", "Hauteur", "Triple"]
    famille["lancers"] = ["Javelot", "Poids", "Disque", "Marteau"]
    famille["epcomb"] = ["Heptathlon", "Decathlon"]

    dataframe = dataframe[dataframe["categorie"].str.startswith("JU")|dataframe["categorie"].str.startswith("CA")]
    dataframe = dataframe[dataframe["departement"]==31]
    dataframe = dataframe.copy()
    dataframe["categorie"] = dataframe["categorie"].str.split("/").str[0]
    for key in famille.keys():
        for ep in famille[key]:
            dataframe.loc[dataframe["epreuve"].str.contains(ep), "famille"] = key
    dataframe.loc[dataframe["epreuve"].str.contains("X"), "famille"] = "relais"
    dataframe.loc[dataframe["famille"] == "epcomb", "points"] = pd.to_numeric(dataframe[dataframe["famille"] == "epcomb"]["performance"].str.replace(" pts", "").str.replace(" ", ""), errors="coerce")
    dataframe = dataframe.dropna(subset=["points"])   
    dataframe = (
        dataframe.sort_values("points", ascending=False)
        .drop_duplicates(subset=["id", "epreuve"], keep="first")
    )

    dataframe["place_challenge"] = (
        dataframe.groupby(["epreuve", "categorie"])["points"]
        .rank(method="min", ascending=False)
        .astype(int))

    nombre_familles = dataframe.groupby("id")["famille"].transform("nunique")
    mask = (dataframe["famille"] != "epcomb") | (nombre_familles >= 3)
    dataframe = dataframe[mask]
    
    mask_keep_all = dataframe["famille"].isin(["epcomb", "marche"])
    mask_dup = dataframe.duplicated(subset=["id", "famille"], keep=False)
    dataframe = dataframe[mask_keep_all | mask_dup]
    
    points_map = {1: 100, 2: 80, 3: 60, 4: 50, 5: 40, 6: 30, 7: 20, 8: 10}
    dataframe["points_challenge"] = dataframe["place_challenge"].map(points_map).fillna(0)
    dataframe["points_challenge_bonus"] = dataframe["points_challenge"]
    
    dataframe.loc[dataframe["niveau"].str.startswith("R", na=False), "points_challenge_bonus"] += 10
    dataframe.loc[dataframe["niveau"].str.startswith("IR", na=False), "points_challenge_bonus"] += 20
    dataframe.loc[dataframe["niveau"].str.startswith("N", na=False), "points_challenge_bonus"] += 30

    dataframe["points_cumul_challenge"] = (
        dataframe.groupby(["id", "famille"])["points_challenge_bonus"]
        .transform(lambda x: x.nlargest(2).sum())
    )

    return dataframe


def cli():
    parser = argparse.ArgumentParser(
        "athle-challenges-cli", description="Interface en ligne de commande pour athle-challenges"
    )

    parser.add_argument(
        "-csv-in",
        help="Resultats des competitions",
        required=True
    )

    parser.add_argument(
        "-out_dir",
        help="Resultats du challenge",
        default="challenge"
    )

    parser.add_argument(
        '-challenge',
        choices=['BEMI', 'CAJU'],
        default="BEMI")

    args = parser.parse_args()
    dataframe = pd.read_csv(args.csv_in)
    if args.challenge == "BEMI":
        indiv, equipes = main_bemi(dataframe)
        if not os.path.exists(args.out_dir):
            os.makedirs(args.out_dir)
        indiv.to_csv(os.path.join(args.out_dir, "individuels.csv"))
        equipes.to_csv(os.path.join(args.out_dir, "equipes.csv"))

    if args.challenge == "CAJU":
        resultats = main_caju(dataframe)
        if not os.path.exists(args.out_dir):
            os.makedirs(args.out_dir)
        resultats.to_csv(os.path.join(args.out_dir, "resultats.csv"))
    
if __name__ == "__main__":
    cli()
