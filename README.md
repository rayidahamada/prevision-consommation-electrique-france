# Prévision de la consommation électrique en France

Projet universitaire M1 MIASHS 2026–2027 : prévision de la consommation électrique en France à l'aide du Machine Learning.

L'objectif est de prévoir la consommation électrique française sur un horizon de **24 heures**. La source envisagée est RTE / ODRÉ ; le jeu de données précis, sa licence, sa granularité et ses conditions d'accès seront documentés lors de sa sélection. Aucune donnée n'a encore été téléchargée.

Les approches envisagées sont la régression linéaire, Random Forest et Gradient Boosting. Leur comparaison utilisera des découpages chronologiques, en veillant à n'utiliser que les informations disponibles au moment de la prévision.

## Objectifs

- Explorer et documenter les données de consommation électrique.
- Préparer des variables explicatives et des jeux de données reproductibles.
- Comparer ultérieurement des méthodes de prévision en respectant l'ordre temporel.
- Évaluer les performances et présenter les limites des résultats.

Le projet est à son stade d'initialisation. Aucune donnée n'a été téléchargée, aucun modèle entraîné et aucun résultat produit.

## Outils

Python, NumPy, pandas, Matplotlib, scikit-learn, Jupyter et ipykernel ; Git et GitHub pour le suivi des versions.

## Structure

```text
data/
  raw/              # Données sources, ignorées par Git
  processed/        # Données préparées
notebooks/          # Analyses exploratoires
src/                # Code réutilisable
models/             # Modèles à venir
reports/
  environnement.md  # Environnement et limites de reproductibilité
  figures/          # Figures des rapports
tests/              # Tests à venir
requirements.txt    # Dépendances directes
AGENTS.md           # Règles de développement
```

Les dossiers vides sont conservés avec des fichiers `.gitkeep`. Ne pas ajouter de données volumineuses, confidentielles ou de secrets au dépôt.

Les artefacts générés dans `models/` sont exclus de Git ; seuls `.gitkeep` et un éventuel `README.md` y sont autorisés par les règles actuelles. Les extensions usuelles de modèles sérialisés sont également ignorées dans tout le dépôt. La provenance et les procédures de génération des futurs modèles devront être documentées sans publier leurs binaires.

## Installation sous Windows / PowerShell

Depuis la racine du projet, utiliser un interpréteur Python fonctionnel :

La création de `.venv` ci-dessous concerne une nouvelle installation. Si cet environnement existe déjà, utiliser directement son interpréteur sans le recréer.

```powershell
python --version
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip check
```

Si `python` pointe vers un alias Windows inutilisable, remplacer la commande de création par le chemin d'un Python installé. Dans cet environnement :

```powershell
& "$env:USERPROFILE\anaconda3\python.exe" -m venv .venv
```

L'environnement local utilise Python 3.14.6. L'utilisateur a confirmé l'installation des six dépendances ainsi que la réussite de `pip check` et des imports dans son terminal PowerShell. Les versions ne sont pas figées : une installation future pourra résoudre des versions différentes. Voir [la documentation de l'environnement](reports/environnement.md) pour la portée de ces validations et les limites de reproductibilité.

Dans VS Code, sélectionner `.venv\Scripts\python.exe` avec **Python: Select Interpreter**, puis sélectionner ce même environnement pour les notebooks.

## Lancer Jupyter et vérifier les imports

```powershell
.\.venv\Scripts\python.exe -m jupyter lab
.\.venv\Scripts\python.exe -c "import numpy, pandas, matplotlib, sklearn, jupyter, ipykernel; print('Imports OK')"
```

## Versionnement

Dépôt distant : https://github.com/rayidahamada/prevision-consommation-electrique-france

Le dépôt local est initialisé sur `main` et `origin` pointe vers ce dépôt GitHub. Aucun commit ni push n'a été réalisé à ce stade. Toute création de commit ou publication nécessite une validation explicite. Avant un premier push, vérifier le contenu du dépôt distant et intégrer son éventuel historique sans l'écraser.
