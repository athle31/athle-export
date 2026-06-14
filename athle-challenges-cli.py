#!/usr/bin/env python
import argparse
import os
import pandas as pd

pd.set_option('display.max_columns', None)

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
    dataframe["club.keep"] = dataframe["club"]
    dataframe = dataframe.groupby(["club", "unisexe"],
                                  group_keys=True).apply(total_club).reset_index(drop=True) 
    dataframe = dataframe.sort_values(by="points", ascending=False)
    dataframe.drop(columns=["calcul", "sexe", "categorie", "nom/prenom"], inplace=True)
    dataframe.drop_duplicates(inplace=True)
    equipes = dataframe.copy()
    equipes = equipes.rename(columns={"unisexe": "categorie"})
    dataframe["club"] = dataframe["club.keep"]

    equipes = equipes.loc[:, ["club", "points", "categorie", "membres", "departement", "region", "epreuve"]]

    
    return indiv, equipes


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
    
if __name__ == "__main__":
    cli()
