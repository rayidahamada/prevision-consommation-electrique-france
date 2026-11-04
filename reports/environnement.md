# Environnement Python et reproductibilité

## Environnement déclaré et validations

Le projet utilise un environnement virtuel local `.venv` avec **Python 3.14.6**. Cet environnement est exclu du suivi Git.

Dans le contexte de la mission 003, l'utilisateur a confirmé depuis son terminal PowerShell :

- l'installation réussie de NumPy, pandas, Matplotlib, scikit-learn, Jupyter et ipykernel ;
- le résultat `No broken requirements found.` pour `python -m pip check` ;
- la réussite des imports des six bibliothèques.

Ces validations sont rapportées par l'utilisateur. Elles ne constituent pas des tests d'analyse, de prévision ou de performance. Aucun résultat scientifique n'a été produit.

## Dépendances

`requirements.txt` déclare les six dépendances directes nécessaires. Il ne contient pas de versions figées et ne décrit pas toutes les dépendances transitives. pip choisit les distributions disponibles satisfaisant les contraintes déclarées au moment de l'installation.

Une nouvelle installation peut donc différer selon la date, le système, l'architecture et les distributions disponibles pour Python 3.14.6. La validation locale rapportée ne garantit pas la reproductibilité exacte sur un autre poste. `pip check` vérifie la cohérence des dépendances déclarées des paquets installés ; les imports vérifient leur chargement, sans valider tous leurs comportements.

Un relevé des versions ou un fichier de verrouillage pourra être ajouté dans une étape ultérieure après examen. Aucun numéro de version de bibliothèque n'est inventé ni modifié dans cette mission.

## Commandes de contrôle

Depuis la racine du projet, pour utiliser explicitement l'environnement virtuel :

```powershell
.\.venv\Scripts\python.exe --version
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -c "import numpy, pandas, matplotlib, sklearn, jupyter, ipykernel; print('Imports OK')"
.\.venv\Scripts\python.exe -m pip list
```

Ces commandes sont fournies pour vérification ; leur présence dans ce document ne signifie pas qu'elles ont été exécutées par Codex durant cet audit.
