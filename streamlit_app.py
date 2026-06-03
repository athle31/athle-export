import streamlit as st
import numpy as np
import datetime
import importlib
import logging
athle_export = importlib.import_module("athle-export-cli")


st.image("logo.png")

categories = st.multiselect(
    "Categories", ["BE", "MI"],
    default=["BE", "MI"],
    accept_new_options=True)
structure = st.text_input('Structure', "031")

annees = map(str, np.arange(2004, datetime.date.today().year+1))
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

        dataframe = athle_export.main(categories, annee, structure, logger=logger)
        st.session_state.logs = []
        log_placeholder.code("")
        logger.info("Export reussi !")

        st.download_button(
            label="Télécharger en csv",
            data=dataframe.to_csv(),
            file_name='bilan.csv',
            mime='text/csv'
        )
