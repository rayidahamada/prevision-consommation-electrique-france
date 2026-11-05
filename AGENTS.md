# Règles de développement avec Codex

## Contexte

Projet universitaire M1 MIASHS 2026–2027 : prévision de la consommation électrique en France par Machine Learning.

## Protection du travail et autorisations

- Examiner les fichiers existants et l'état Git avant toute modification.
- Ne pas supprimer ni écraser le travail existant sans autorisation explicite.
- Ne pas créer de commit, effectuer de push, publier ni modifier le dépôt distant sans validation explicite de l'utilisateur.
- Ne jamais contourner les restrictions de sécurité ; signaler les blocages.
- Ne pas exposer de jetons, mots de passe ou données personnelles.
- Ne pas télécharger de données RTE ni entraîner de modèles sans demande explicite.

## Organisation et reproductibilité

- Placer le code réutilisable dans `src/`, les analyses dans `notebooks/` et les tests dans `tests/`.
- Utiliser `.venv` et déclarer les dépendances dans `requirements.txt`.
- Ne pas versionner l'environnement virtuel, les secrets ou les données brutes.
- Documenter la provenance, la licence, les unités et les transformations des données lorsqu'elles seront introduites.
- Ne jamais inventer de données, de résultats ou de validations.
- Pour les prévisions, respecter la chronologie et éviter les fuites de données entre entraînement et évaluation.
- Garder les chemins portables et documenter les commandes nécessaires.

## Vérification et communication

- Exécuter les contrôles pertinents pour les changements réalisés.
- Distinguer les vérifications réussies, les échecs et les contrôles impossibles.
- Présenter en français les changements, les commandes et les limites.

## Qualité rédactionnelle et documentaire

- Rédiger le README et les rapports dans un français académique, clair, impersonnel et naturel.
- Ne pas désigner le responsable du projet comme « l'utilisateur » ou « l'étudiant » dans les textes destinés à être publiés.
- Éviter les formulations de dialogue avec un assistant, les commentaires sur la génération du texte et les instructions de pilotage internes.
- Réserver les consignes destinées à Codex à `AGENTS.md`, sauf lorsqu'elles sont nécessaires à la reproductibilité.
- Distinguer les résultats effectivement vérifiés, les déclarations du responsable du projet, les hypothèses scientifiques et les opérations non réalisées.
- Dater les constats susceptibles de devenir obsolètes.
- Ne jamais transformer une incertitude scientifique en certitude pour améliorer le style.
- Préserver les faits historiques, les échecs, les sources et la traçabilité.
- Vérifier que les gabarits Python ne réintroduisent pas d'anciennes formulations lors d'une exécution.
- Relire les textes destinés à GitHub avant toute proposition de commit ; exécuter `python scripts/check_documentation.py` et examiner les avertissements sans réécrire automatiquement les constats historiques.
