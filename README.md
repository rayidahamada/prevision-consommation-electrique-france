# Prévision de la consommation électrique en France

Projet universitaire M1 MIASHS 2026–2027 : prévision de la consommation électrique en France à l'aide du Machine Learning.

L'objectif est de prévoir la consommation électrique française sur les **24 prochaines heures**, à partir de données officielles RTE diffusées par ODRÉ. Le périmètre étudié est la France métropolitaine hors Corse.

Le terme « J+1 » désigne ici l'objectif général du projet : la définition de l'instant d'émission et de la fenêtre cible reste à valider. Une fenêtre de 24 heures écoulées ne correspond pas toujours au jour civil français suivant, qui peut compter 23 ou 25 heures aux changements d'heure.

Source officielle : [ODRÉ — Consommation quotidienne brute](https://odre.opendatasoft.com/explore/dataset/consommation-quotidienne-brute/). Le champ électrique est publié en MW au pas demi-horaire. Les colonnes gazières du même jeu ne constituent pas la cible électrique. La licence indiquée est la Licence Ouverte 2.0 ; la provenance et la date de mise à jour de la version réutilisée doivent rester documentées.

Les approches envisagées sont la régression linéaire, Random Forest et Gradient Boosting. Leur comparaison utilisera des découpages chronologiques, en veillant à n'utiliser que les informations disponibles au moment de la prévision.

## Objectifs

- Explorer et documenter les données de consommation électrique.
- Préparer des variables explicatives et des jeux de données reproductibles.
- Comparer ultérieurement des méthodes de prévision en respectant l'ordre temporel.
- Évaluer les performances et présenter les limites des résultats.

## État actuel

- Un instantané a été acquis le 4 novembre 2026 et audité : **258 576 observations**, avec une dernière observation au 30 septembre 2026. Son empreinte et sa provenance sont conservées dans les rapports.
- Les doublons temporels, puissances contradictoires, créneaux absents et statuts manquants ont été diagnostiqués.
- Une grille UTC régulière de 30 minutes a été préparée, avec qualité et provenance : **258 574 créneaux**, dont **258 521 avec une puissance disponible**, **22 ambigus** et **31 absents**. Les 1 440 statuts RTE manquants sont conservés sans remplacement.
- Deux séries horaires **expérimentales distinctes** ont été produites sur les mêmes bornes, sous les hypothèses d'étiquette de début et de fin d'intervalle. Aucune n'est présentée comme la convention physique confirmée par RTE.
- Des tests automatisés couvrent l'acquisition simulée, l'audit et les préparations sur données synthétiques. Les résultats d'exécution sont consignés dans les rapports de mission.

Aucune EDA, construction de variables prédictives, modélisation ou évaluation de performances n'a encore été réalisée.

## Limites scientifiques ouvertes

Le rattachement début/fin d'intervalle des observations ODRÉ et la constance de leurs conventions historiques ne sont pas confirmés. La documentation éCO2mix distingue puissances instantanées et moyennes, mais sa transposition exacte à cet export reste à établir. Les scénarios horaires supposent une puissance moyenne demi-horaire et restent des constructions expérimentales.

Les absences et conflits ne sont pas imputés ; les flags et statuts restent traçables. La disponibilité des données et de leurs révisions à l'instant d'une prévision historique reste une question distincte de leur date d'observation. L'accès API est bloqué depuis l'environnement Codex lors des derniers contrôles : les informations externes communiquées ne prouvent pas l'identité de toutes les observations distantes.

## Outils

Python, NumPy, pandas, Matplotlib, scikit-learn, Jupyter et ipykernel ; Git et GitHub pour le suivi des versions.

## Structure

```text
data/
  raw/              # Données sources, ignorées par Git
  processed/        # Grille et CSV expérimentaux générés, ignorés par Git
notebooks/          # Analyses exploratoires
src/                # Acquisition, audit et préparations reproductibles
models/             # Modèles à venir
reports/
  environnement.md  # Environnement et limites de reproductibilité
  figures/          # Figures des rapports
tests/              # Tests unitaires sur données synthétiques
requirements.txt    # Dépendances directes
AGENTS.md           # Règles de développement
```

Les dossiers vides sont conservés avec des fichiers `.gitkeep`. Ne pas ajouter de données volumineuses, confidentielles ou de secrets au dépôt.

**Les données brutes, la grille demi-horaire et les CSV horaires ne sont pas disponibles dans GitHub.** Un clone ne fournit donc pas l'instantané historique. Sa reproduction exacte exige l'accès à une copie conservée séparément et la vérification de son SHA-256. Une nouvelle acquisition depuis le portail vivant peut contenir des données différentes.

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

## Vérifier l'environnement et lancer les tests

```powershell
.\.venv\Scripts\python.exe -c "import numpy, pandas, matplotlib, sklearn, jupyter, ipykernel; print('Imports OK')"
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Exécuter ces commandes depuis la racine du dépôt. Les tests sont synthétiques ; ils ne prouvent ni l'accès au portail ni une convention physique des données. Aucun notebook d'analyse n'est encore livré.

## Scripts et reproduction des préparations

- [Acquisition et audit](src/odre_data.py) : téléchargement officiel vers un nouveau dossier `data/raw/odre_*`, manifeste et audit JSON local.
- [Diagnostic temporel](src/diagnostic_temporel.py) : diagnostic de l'instantané historique, avec assertions propres à cette version.
- [Préparation demi-horaire](src/preparer_electricite.py) : grille UTC, traitement explicite des conflits/absences et provenance.
- [Préparation horaire expérimentale](src/preparer_horaire_experimental.py) : deux hypothèses séparées, qualité et bornes communes.

Consulter les commandes réellement utilisées dans les rapports ci-dessous. Les scripts de préparation offrent des chemins explicites et refusent d'écraser leurs sorties. Ne pas relancer une acquisition volumineuse ou une reconstruction sans validation de la version et des chemins ; aucun téléchargement automatique n'est déclenché par le dépôt.

## Principaux rapports

- [Environnement Python et reproductibilité](reports/environnement.md).
- [Étude initiale des données et du protocole](reports/etude_donnees_rte.md).
- [Acquisition et audit qualité](reports/audit_qualite_donnees.md) et [résultats de l'audit local](reports/audit_observations.json).
- [Diagnostic des anomalies temporelles](reports/diagnostic_anomalies_temporelles.md).
- [Préparation demi-horaire contrôlée](reports/preparation_electricite_phase1.md).
- [Étude des conventions et de l'agrégation](reports/etude_agregation_horaire.md).
- [Préparation horaire expérimentale A/B](reports/preparation_horaire_experimentale.md).
- [Audit des mises à jour et de Git, avec complément externe](reports/mission_009_audit_mises_a_jour_et_git.md).
- [Corrections documentaires et préparation du commit](reports/mission_009_bis_preparation_commit.md).

Les rapports sont datés et peuvent décrire des états historiques : lire leurs compléments pour connaître les vérifications ultérieures. Les limites et hypothèses ne constituent pas des résultats de prévision.

## Prochaines étapes du projet

1. Valider le protocole de cible et les limites des scénarios expérimentaux.
2. Réaliser l'analyse exploratoire (EDA).
3. Construire les variables explicatives en respectant leur disponibilité à l'origine.
4. Entraîner les modèles envisagés et des références naïves.
5. Effectuer une validation chronologique, puis une évaluation finale sur un test réservé, avec MAE et RMSE.

Ces étapes sont prévues ; aucun résultat prédictif n'est annoncé à ce stade.

## Versionnement

Dépôt distant : https://github.com/rayidahamada/prevision-consommation-electrique-france

Le dépôt est initialisé sur `main` et un premier commit existe. Les missions d'audit ont relevé des scripts, tests et rapports encore non suivis : leur préparation documentaire ne signifie pas qu'ils sont déjà publiés. Toute mise en index, création de commit ou publication nécessite la validation explicite de l'utilisateur. Ne jamais écraser l'historique distant.
