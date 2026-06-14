#!/usr/bin/env python
import datetime
import argparse
import os, re
import numpy as np
import pandas as pd
import requests
import logging
from io import StringIO

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)

def get_html_content(url, logger):
    try:
        html = StringIO(requests.get(url).text)
    except requests.exceptions.ConnectionError:
        logger.error("No internet connection")
        return None
    return html

def get_nb_pages(url, logger):
    html = get_html_content(url, logger)
    df = pd.read_html(html)[0]
    match = re.search(r"/\s*(\d+)", df.iloc[1, 0])
    return int(match.group(1)) if match else 1

def get_page_as_dataframe_bilan(url, page, logger):
    url_page = url+"&frmposition="+str(page)
    df = pd.read_html(get_html_content(url_page, logger), extract_links="all")[0]
    df.dropna(subset=4, inplace=True)
    df.columns = ["place", "performance", "nom/prenom", "club", "region", "departement", "categorie", "date", "lieu", "epreuve"]
    for col in df.columns:
        if col != "nom/prenom":
            df[col] = df[col].str[0]
    df["id"] = df["nom/prenom"].str[1]
    df["nom/prenom"] = df["nom/prenom"].str[0]
    df.loc[~df["epreuve"].str.contains(r"\|", na=False), "epreuve"] = np.nan
    df["epreuve"] = df["epreuve"].ffill()
    df["epreuve"] = df["epreuve"].str.split("/").str[0].str.strip()
    df = df.iloc[4:-1]
    df["place"] = df["place"].replace("-", 0)
    df = df[pd.to_numeric(df["place"], errors="coerce").notna()]
    df["place"] = df["place"].replace(0, pd.NA).ffill()
    return df

def get_page_as_dataframe_resultats(url, page, competition, logger):
    url_page = url+"&frmposition="+str(page)
    df = pd.read_html(get_html_content(url_page, logger), extract_links="all")[0]
    df.dropna(subset=4, inplace=True)
    df.columns = ["place", "performance", "nom/prenom", "club", "departement", "region", "categorie", "epreuve", "points", "vent"]
    for col in df.columns:
        if col != "nom/prenom":
            df[col] = df[col].str[0]
    df["id"] = df["nom/prenom"].str[1]
    df["nom/prenom"] = df["nom/prenom"].str[0]
    df["niveau"] = df["epreuve"]
    df.loc[~df["epreuve"].str.contains(r"\|", na=False), "epreuve"] = np.nan
    df["epreuve"] = df["epreuve"].ffill()
    df["epreuve"] = df["epreuve"].str.split("/").str[0].str.strip()
    df["vent"] = df["vent"].ffill()
    df["vent"] = df["vent"].str.extract(r"Vt\s*:\s*([-+]?\d+\.?\d*)")
    df = df.iloc[4:-1]
    df["place"] = df["place"].replace("-", 0)
    df = df[pd.to_numeric(df["place"], errors="coerce").notna()]
    df["place"] = df["place"].replace(0, pd.NA).ffill()
    df["competition"] = competition
    return df


def get_page_as_dataframe_competitions(url, page, logger):
    url_page = url+"&frmposition="+str(page)
    df = pd.read_html(get_html_content(url_page, logger), extract_links="all")[0]
    df.dropna(subset=4, inplace=True)
    df.columns = ["date", "libelle", "lieu", "type", "niveau", "label", "fiche", "resultats", "tmp"]
    df.drop(["label", "fiche", "resultats", "tmp"], axis='columns', inplace=True)
    for col in df.columns:
        if col != "libelle":
            df[col] = df[col].str[0]
    df["frm"] = df["libelle"].str[1]
    df["frm"] = df["frm"].str.extract(r"frmcompetition=(\d+)")
    df["libelle"] = df["libelle"].str[0]
    df = df.dropna()
    df = df.loc[:, ["date", "frm", "libelle", "lieu", "type", "niveau"]]
    return df


def main_bilan(categories, annee, structure=None, logger=None):
    if logger is None:
        logger = logging

    if structure == "":
        structure = None

    frmstructure = None
    try:
        int(structure)
        if len(structure) == 3:
            frmstructure = "&frmdepartement="+structure
            logger.info("Mode departement ("+structure+")")
        elif len(structure) == 6:
            frmstructure = "&frmclub="+structure
            logger.info("Mode club ("+structure+")")
    except ValueError:
        frmstructure = "&frmligue="+structure
        logger.info("Mode ligue ("+structure+")")
    except TypeError:
        frmstructure = "&frmplaces=100"
        logger.info("Mode Top 100 France")

    dataframes = []
    for cat in categories:
        for sex in ["M", "F"]:
            logger.info("Recherche pour les "+cat+sex)
            url = "https://www.athle.fr/bases/liste.aspx?frmpostback=true&frmbase=bilans&frmmode=1&frmespace=0&frmannee="+annee+"&frmcategorie="+cat+"&frmsexe="+sex+frmstructure

            logger.info(url)

            try:
                nb_pages = get_nb_pages(url, logger)
            except ValueError:
                logger.info("Pas de pages trouvees")
                nb_pages = 0
            logger.info("Nombre de pages : "+str(nb_pages))
            for page in range(nb_pages):
                dataframes.append(get_page_as_dataframe_bilan(url,
                                                              page,
                                                              logger))

    try:
        dataframe = pd.concat(dataframes)
    except ValueError:
        logger.info("Resultats introuvables")
        dataframe = pd.DataFrame()
    logger.info(str(len(dataframe))+" resultats")
    return dataframe

def main_resultats(competitions, logger=None):
    if logger is None:
        logger = logging

    dataframes = []
    for competition in competitions:
        logger.info("Recherche pour la competition "+competition)
        url = "https://www.athle.fr/bases/liste.aspx?frmbase=resultats&frmmode=1&frmespace=0&frmcompetition="+str(competition)
        logger.info(url)
        try:
            nb_pages = get_nb_pages(url, logger)
        except ValueError:
            logger.info("Pas de pages trouvees")
            nb_pages = 0

        logger.info("Nombre de pages : "+str(nb_pages))
        for page in range(nb_pages):
            dataframes.append(get_page_as_dataframe_resultats(url, page, competition, logger))

    try:
        dataframe = pd.concat(dataframes)
    except ValueError:
        logger.info("Resultats introuvable")
        dataframe = pd.DataFrame()
    logger.info(str(len(dataframe))+" resultats")
    return dataframe


mois = {
    "janvier": 1,
    "février": 2,
    "mars": 3,
    "avril": 4,
    "mai": 5,
    "juin": 6,
    "juillet": 7,
    "août": 8,
    "septembre": 9,
    "octobre": 10,
    "novembre": 11,
    "décembre": 12,
}

def parse_date(s):
    jour, mois_nom = s.split()
    jour = int(jour.split("-")[0])
    return pd.Timestamp(year=2025, month=mois[mois_nom], day=jour)

def main_competitions(saison, logger=None):
    if logger is None:
        logger = logging

    dataframes = []
    logger.info("Recherche des competitions du 31/32/82")

    for dep in [31, 32, 82]:
        url = "https://www.athle.fr/bases/liste.aspx?frmpostback=true&frmbase=resultats&frmmode=2&frmespace=0&frmsaison="+str(saison)+"&frmdate1=&frmdate2=&frmtype1=Stade&frmniveau=D%C3%A9partemental&frmligue=OCC&frmdepartement=0"+str(dep)+"&frmniveaulab=&frmeprrch=&frmtype2=Championnat&frmtype3=&frmtype4=&frmclub="
        logger.info(url)
        try:
            nb_pages = get_nb_pages(url, logger)
        except ValueError:
            logger.info("Pas de pages trouvees")
            nb_pages = 0

        logger.info("Nombre de pages : "+str(nb_pages))
        for page in range(nb_pages):
            dataframes.append(get_page_as_dataframe_competitions(url, page, logger))

    try:
        dataframe = pd.concat(dataframes)
        dataframe["date"] = dataframe["date"].apply(parse_date)
        dataframe = dataframe.sort_values("date")
    except ValueError:
        logger.info("Resultats introuvables")
        dataframe = pd.DataFrame()
    logger.info(str(len(dataframe))+" resultats")
    return dataframe


def cli():
    parser = argparse.ArgumentParser(
        "athle-export-cli", description="Interface en ligne de commande pour athle-export"
    )

    subparsers = parser.add_subparsers(help='mode', required=True, dest="mode")

    parser_bilan = subparsers.add_parser('bilan', help="Bilan")
    
    parser_bilan.add_argument(
        '-categories',
        choices=['BE', 'MI'],
        nargs="+",
        help="Categories",
        default=['BE', 'MI'])

    parser_bilan.add_argument(
        "-structure",
        help="Structure (par defaut: 100 premiers au bilan FFA)"
    )

    parser_bilan.add_argument(
        "-annee",
        help="Annee",
        default=str(datetime.date.today().year)
    )

    parser_bilan.add_argument(
        "-csv",
        help="Fichier CSV",
        default="bilan.csv"
    )

    parser_resultats = subparsers.add_parser('resultats', help="Resultats")
    parser_resultats.add_argument(
        '-competitions',
        nargs="+",
        help="Competitions",
        required=True)

    parser_resultats.add_argument(
        "-csv",
        help="Fichier CSV",
        default="resultats.csv"
    )

    parser_competitions = subparsers.add_parser('competitions', help="Competitions")
    parser_competitions.add_argument(
        "-annee",
        help="Annee",
        default=str(datetime.date.today().year)
    )

    args = parser.parse_args()
    
    if args.mode == "bilan":
        dataframe = main_bilan(args.categories, args.annee, args.structure)
        dataframe.to_csv(args.csv)
        return dataframe
    elif args.mode == "resultats":
        dataframe = main_resultats(args.competitions)
        dataframe.to_csv(args.csv)
        return dataframe
    elif args.mode == "competitions":
        dataframe = main_competitions(args.annee)

if __name__ == "__main__":
    cli()
