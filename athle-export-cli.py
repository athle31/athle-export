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

def get_page_as_dataframe(url, page, logger):
    url_page = url+"&frmposition="+str(page)
    df = pd.read_html(get_html_content(url_page, logger))[0]
    df.dropna(subset=4, inplace=True)
    df.columns = ["place", "performance", "nom/prenom", "club", "region", "departement", "categorie", "date", "lieu", "epreuve"]
    df.loc[~df["epreuve"].str.contains(r"\|", na=False), "epreuve"] = np.nan
    df["epreuve"] = df["epreuve"].ffill()
    df = df.iloc[4:-1]
    df["place"] = df["place"].replace("-", 0)
    df = df[pd.to_numeric(df["place"], errors="coerce").notna()]
    df["place"] = df["place"].replace(0, pd.NA).ffill()
    return df

def main(categories, annee, structure=None, logger=None):
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

            nb_pages = get_nb_pages(url, logger)
            logger.info("Nombre de pages : "+str(nb_pages))
            for page in range(nb_pages):
                dataframes.append(get_page_as_dataframe(url, page, logger))

    dataframe = pd.concat(dataframes)
    logger.info(str(len(dataframe))+" resultats")
    return dataframe

def cli():
    parser = argparse.ArgumentParser(
        "athle-export-cli", description="Interface en ligne de commande pour athle-export"
    )
    parser.add_argument(
        '-categories',
        choices=['BE', 'MI'],
        nargs="+",
        help="Categories",
        default=['BE', 'MI'])

    parser.add_argument(
        "-structure",
        help="Structure (par defaut: 100 premiers au bilan FFA)"
    )

    parser.add_argument(
        "-annee",
        help="Annee",
        default=str(datetime.date.today().year)
    )

    parser.add_argument(
        "-csv",
        help="Fichier CSV",
        default="bilan.csv"
    )

    args = parser.parse_args()

    dataframe = main(args.categories, args.annee, args.structure)
    dataframe.to_csv(args.csv)

if __name__ == "__main__":
    cli()
