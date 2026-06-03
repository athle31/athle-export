<div align="center">
<a target="_blank" href="https://athle-export.streamlit.app">
<picture>
  <img
    src="https://raw.githubusercontent.com/athle31/athle-export/refs/heads/main/logo.png"
    width="50%"
  />
</picture>
</a>
</div>

# 🌐 **En bref**

Cet outil permet de récupérer les bilans FFA sous la forme d'un CSV pour faciliter votre usage.

# 🚀 **Pour démarrer**

### Rendez-vous sur l'outil en ligne

L'outil en ligne est ici : [athle-export.streamlit.app](https://athle-export.streamlit.app)

### Pour les "geeks", clonez le dépôt et utilisez-le en ligne de commande

Pour le télécharger et l'installer :

```
git clone https://github.com/athle31/athle-export.git
cd athle-export && pip install -r requirements.txt
```

Pour l'utiliser :
```
python athle-export-cli.py
```

Par défaut, l'outil calcule le top 100 benjamins et minimes de l'année en cours et l'enregistre dans le fichier "bilan.csv".

```python athle-export-cli.py -h``` permet d'accéder à tous les paramètres en choisissant :
- les catégories : "BE" ou "MI" seulement par exemple
- la structure :
  - par un code de 6 chiffres pour un club (par exemple 031015)
  - par un code de 3 chiffres pour un departement (par exemple 031)
  - par un trigramme pour une ligue (par exemple OCC)
- l'année YYYY par exemple "2026"
- le nom du fichier par exemple "mon_fichier.csv"