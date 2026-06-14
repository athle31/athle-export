import streamlit as st
import pandas as pd
import numpy as np
import datetime
import importlib
import logging
athle_export = importlib.import_module("athle-export-cli")
athle_challenges = importlib.import_module("athle-challenges-cli")

st.image("logo.png")

mode = st.selectbox("Mode", ("Bilan", "Resultats", "Challenges"))

if mode == "Bilan":
    categories = st.multiselect(
        "Categories", ["BE", "MI"],
        default=["BE", "MI"],
        accept_new_options=True)
    structure = st.text_input('Structure', "031")

    annees = map(str, np.arange(2004, datetime.date.today().year+2))
    annee = st.select_slider("Annee", options=annees)

    if st.button("Export en CSV"):
        with st.spinner("Veuillez patienter..."):
            log_placeholder = st.empty()

            if "logs" not in st.session_state:
                st.session_state.logs = []

            class StreamlitHandler(logging.Handler):
                def emit(self, record):
                    msg = self.format(record)
                    st.session_state.logs.append(msg)
                    log_placeholder.code("\n".join(st.session_state.logs))

            logger = logging.getLogger("app")
            logger.setLevel(logging.INFO)

            handler = StreamlitHandler()
            handler.setFormatter(
                logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
            )

            logger.addHandler(handler)

            dataframe = athle_export.main_bilan(categories, annee, structure, logger=logger)
            st.session_state.logs = []
            log_placeholder.code("")
            logger.info("Export reussi !")

            st.download_button(
                label="Telecharger en csv",
                data=dataframe.to_csv(),
                file_name='bilan.csv',
                mime='text/csv'
            )

elif mode == "Resultats":
    annees = map(str, np.arange(2004, datetime.date.today().year+2))
    annee = st.select_slider("Annee", options=annees)

    frm_list = []
    if st.button("Afficher les competitions 31/32/82 de l'annee choisie"):
        with st.spinner("Veuillez patienter..."):
            dataframe = athle_export.main_competitions(annee)
            if len(dataframe) > 0:
                st.session_state.competitions = dataframe
            else:
                st.warning("Pas de competitions trouvees")
            
    if 'competitions' not in st.session_state:
        frm_list = []
    else:
        multiples_options = []
        for index, row in st.session_state.competitions.iterrows():
            multiples_options.append(st.checkbox(str(row["frm"]) + " : "+ str(row["libelle"]) + " ("+str(row["lieu"])+")" ))

        for idx, value in enumerate(st.session_state.competitions["frm"].values):
            if multiples_options[idx]:
                frm_list.append(value)
                    
    competitions = st.multiselect(
        "Competitions", frm_list,
        accept_new_options=True)

    if st.button("Export en CSV"):
        with st.spinner("Veuillez patienter..."):
            log_placeholder = st.empty()

            if "logs" not in st.session_state:
                st.session_state.logs = []

            class StreamlitHandler(logging.Handler):
                def emit(self, record):
                    msg = self.format(record)
                    st.session_state.logs.append(msg)
                    log_placeholder.code("\n".join(st.session_state.logs))

            logger = logging.getLogger("app")
            logger.setLevel(logging.INFO)

            handler = StreamlitHandler()
            handler.setFormatter(
                logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
            )

            logger.addHandler(handler)

            dataframe = athle_export.main_resultats(competitions, logger=logger)
            st.session_state.logs = []
            log_placeholder.code("")
            logger.info("Export reussi !")

            st.download_button(
                label="Telecharger en csv",
                data=dataframe.to_csv(),
                file_name='resultats.csv',
                mime='text/csv'
            )

elif mode == "Challenges":
    resultats = st.file_uploader("Resultats des competitions (BE/MI)", type="csv")
    if resultats is not None:
        dataframe = pd.read_csv(resultats)
        st.dataframe(dataframe)
        indiv, equipes = athle_challenges.main_bemi(dataframe)
        st.info("Resultats du challenge disponibles !")
        st.download_button(
            label="Resultats individuels",
            data=indiv.to_csv(),
            file_name='individuels.csv',
            mime='text/csv'
        )
        st.download_button(
            label="Resultats equipes",
            data=equipes.to_csv(),
            file_name='equipes.csv',
            mime='text/csv'
        )

        for cat in sorted(list(set(indiv["categorie"].values))):
            st.subheader(cat)
            st.dataframe(indiv[indiv["categorie"] == cat].reset_index(drop=True))
            
        for cat in sorted(list(set(equipes["categorie"].values))):
            st.subheader(cat)
            st.dataframe(equipes[equipes["categorie"] == cat].reset_index(drop=True))


    resultats = st.file_uploader("Resultats des competitions (CA/JU)", type="csv")
    if resultats is not None:
        dataframe = pd.read_csv(resultats)
        st.dataframe(dataframe)
        classement = athle_challenges.main_caju(dataframe)
        st.info("Resultats du challenge disponibles !")
        st.download_button(
            label="Resultats",
            data=classement.to_csv(),
            file_name='resultats.csv',
            mime='text/csv'
        )

        for cat in sorted(list(set(classement["categorie"].values))):
            st.subheader(cat)
            for fam in sorted(list(set(classement["famille"].values))):
                st.subheader(fam)
                extract = classement[(classement["categorie"] == cat) & (classement["famille"] == fam)]
                extract = extract.sort_values("points_cumul_challenge",
                                              ascending=False).reset_index(drop=True)
                st.dataframe(extract)

