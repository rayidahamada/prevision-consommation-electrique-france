# Acquisition et audit qualité ODRÉ — Mission 006

> Note de lecture du 5 novembre 2026 : les sections initiales conservent les résultats de la première tentative d'acquisition, qui avait échoué. L'acquisition réussie et l'audit ultérieur sont documentés dans le complément de la section 9. La procédure de la section 8 décrit l'étape alors envisagée et ne constitue pas une nouvelle demande de téléchargement.

Date : 4 novembre 2026. Projet M1 MIASHS 2026–2027.

## 1. État constaté et portée

Avant modification : branche `main` avec suivi local `origin/main`. Le document `reports/etude_donnees_rte.md` de la mission précédente était déjà présent et non suivi ; il a été lu et conservé sans modification. Les règles `AGENTS.md`, le README, les dépendances et la structure ont été examinés. L'autorisation d'acquisition de cette mission permet de préparer et tenter le téléchargement ; elle n'autorise ni modèle ni publication.

**Aucune observation récupérée. Aucun audit numérique de données réelles n'a pu être exécuté.** L'accès Python au portail est interdit par l'environnement : `urllib.error.URLError`, causée par `PermissionError: [WinError 10013]`. Les pages documentaires sont partiellement accessibles via l'outil web ; cela ne rend pas le réseau accessible au script Python. Aucune restriction n'a été contournée.

## 2. Sources réellement consultées

- [Fiche officielle ODRÉ](https://odre.opendatasoft.com/explore/dataset/consommation-quotidienne-brute/) et [vue française indexée](https://odre.opendatasoft.com/explore/dataset/consommation-quotidienne-brute/?flg=fr-fr).
- [Vue anglaise officielle et schéma indexé](https://odre.opendatasoft.com/explore/dataset/consommation-quotidienne-brute/?flg=en-us) : identifiants des champs. L'ouverture directe reste partiellement dynamique ; les extraits indexés peuvent être anciens.
- [Page d'export ODRÉ](https://odre.opendatasoft.com/explore/dataset/consommation-quotidienne-brute/export/?flg=fr-fr) : consultée, mais interface d'export non rendue intégralement.
- [Référencement officiel data.gouv.fr](https://www.data.gouv.fr/datasets/consommation-quotidienne-brute) : attribution, licence et ressources CSV/JSON annoncées.
- [Texte officiel Etalab de la Licence Ouverte 2.0](https://raw.githubusercontent.com/etalab/licence-ouverte/master/LO.md) : texte intégral accessible cette fois, contrairement au lien redirigé de la mission 005.
- [Documentation de l'éditeur, Explore API 2.1](https://help.opendatasoft.com/apis/ods-explore-v2/explore_v2.1.html), consultée dans les résultats de recherche : export par `/catalog/datasets/{dataset_id}/exports/{format}` ; CSV et JSON sont documentés.

L'endpoint de métadonnées ODRÉ a été tenté par l'outil web (inaccessible) et par Python (échec réseau explicite). Aucun total affiché par un moteur de recherche n'est repris comme résultat de l'audit local.

## 3. Schéma documentaire et limites sémantiques

Identifiants relevés dans le schéma officiel indexé :

```text
date_heure
date
heure
consommation_brute_gaz_grtgaz
statut_grtgaz
consommation_brute_gaz_terega
statut_terega
consommation_brute_gaz_totale
consommation_brute_electricite_rte
statut_rte
consommation_brute_totale
flag_ignore
```

Le schéma décrit des consommations numériques, un horodatage `date_heure` et des champs textuels de calendrier/statut. Ces 12 identifiants sont documentaires : ni le nombre de colonnes d'un export acquis ni leur présence effective ne sont vérifiés. Le script impose les trois clés nécessaires à l'audit électrique et relève les autres colonnes réellement rencontrées.

L'électricité RTE est annoncée en MW, au pas de 30 minutes, pour la France métropolitaine hors Corse. Les séries gazières sont horaires en MW PCS 0 °C. Le total multi-énergies est exclu de la cible électrique. Le nom historique `grtgaz` persiste dans l'identifiant du champ NaTran.

La métadonnée de fuseau est UTC. La convention début/fin d'intervalle et la distinction puissance moyenne/instantanée ne sont toujours pas établies. Les champs locaux `date` et `heure` ne servent pas à reconstruire l'index. `flag_ignore` est conservé sans interprétation non documentée. Aucune conversion en MWh ni agrégation horaire n'est appliquée.

## 4. Licence et attribution

La fiche rattache le jeu à la Licence Ouverte 2.0. Le texte Etalab autorise notamment la copie, l'adaptation et la réutilisation, sous condition de mentionner la source et la date de dernière mise à jour de l'information. La réutilisation ne doit pas suggérer une caution officielle ni induire en erreur sur la provenance. Cette licence ne garantit ni l'absence d'erreurs ni la continuité du service.

Attribution à conserver : **NaTran, RTE, Teréga — ODRÉ ; série électrique : RTE**, avec URL de la fiche et date de mise à jour de l'instantané effectivement employé. La date d'acquisition ne remplace pas la date de mise à jour du producteur. Le manifeste prévoit la métadonnée `modified`, les en-têtes HTTP disponibles et la sauvegarde complète des métadonnées ; si une date manque ou est ambiguë, la vérifier avant diffusion de travaux dérivés.

Les quotas, la disponibilité effective et les autres paramètres de l'API ODRÉ ne sont pas vérifiés de bout en bout. Le script ne fournit aucun identifiant et n'effectue aucune tentative de contournement en cas de refus.

## 5. Acquisition reproductible préparée

Fichier : `src/odre_data.py`, bibliothèque standard Python uniquement ; aucun changement à `requirements.txt`.

URL préparée pour un export JSON intégral, sans filtre :

```text
https://odre.opendatasoft.com/api/explore/v2.1/catalog/datasets/consommation-quotidienne-brute/exports/json
```

Cet endpoint suit la documentation de l'éditeur ; il n'a pas été validé par un export réel dans cet environnement. Le choix de l'export intégral conserve électricité, gaz, statuts et calendrier pour l'audit ; aucun découpage scientifique n'est fixé par l'acquisition.

Chaque exécution réserve un nouveau sous-dossier `data/raw/odre_*`. Elle récupère d'abord les métadonnées, contrôle les champs électriques et la désignation de licence v2, puis écrit l'export dans un fichier `.part`. Après validation minimale du JSON, celui-ci devient `observations.json`. Un manifeste conserve URL, dates UTC, attribution, licence, taille, nombre de lignes et empreinte SHA-256 en cas de succès. Une exécution échouée conserve un manifeste `incomplete` et, éventuellement, un fichier partiel : ne pas les traiter comme un jeu acquis.

Les fichiers précédents ne sont pas remplacés ; aucune option de forçage n'existe. Une nouvelle acquisition peut néanmoins différer si le producteur révise les données : l'empreinte et les métadonnées permettent d'identifier l'instantané, pas de garantir que le serveur restitue une ancienne version. Le chargement JSON d'audit utilise la mémoire et convient à l'échelle annoncée du candidat ; ce n'est pas une solution pour des exports arbitrairement volumineux.

## 6. Exécutions réelles et résultats impossibles

Commandes exécutées :

```powershell
.\.venv\Scripts\python.exe --version
.\.venv\Scripts\python.exe -m src.odre_data --help
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m src.odre_data download
```

- Python : **3.14.6** ; aide du programme : réussie.
- Dernière suite : **9 tests réussis** sur données synthétiques et réponses réseau simulées.
- Acquisition réelle : échec `URLError` dès les métadonnées ; manifeste `data/raw/odre_fdvkshr3/manifest.json`, statut `incomplete`. Aucun fichier d'observations créé. La tentative directe préalable a identifié `WinError 10013`.

| Contrôle sur les observations officielles | Résultat de cette mission |
|---|---|
| Nombre de lignes et colonnes | Non calculable : aucun export acquis |
| Bornes et fréquence observée | Non calculables |
| Valeurs manquantes et doublons temporels | Non calculables |
| Distribution des statuts, min/max et valeurs suspectes | Non calculables |
| Unités et séparation électricité/gaz | Vérification documentaire seulement |
| Début/fin d'intervalle, moyenne/instantané | Non confirmés |

Le zéro observation récupérée décrit l'échec de l'acquisition, pas la taille du jeu officiel.

## 7. Audit automatisé et tests

La commande locale `audit` relève lignes, colonnes, clés absentes, valeurs nulles/vides, horodatages invalides ou sans fuseau, ordre d'origine, doublons après normalisation UTC et intervalles entre dates uniques. Elle compte les créneaux demi-horaires absents entre les bornes observées, séparément pour toutes les lignes et les valeurs électriques finies. Ce contrôle de grille n'établit pas une convention physique d'intervalle.

Elle relève valeurs électriques non numériques/non finies, négatives ou nulles, min/max, statuts RTE et colonnes gazières. Zéros et négatifs sont signalés à examiner, sans être automatiquement supprimés ; aucun seuil haut physique n'est inventé. Les trous hors des bornes observées ne sont pas détectables sans couverture attendue externe.

Les neuf tests couvrent : offsets et heure locale répétée ; rejet d'horodatages sans fuseau ; trous/doublons/manquants électriques ; valeurs non finies/non numériques et séparation gaz ; ordre/horodatages invalides/grille ; schéma JSON et refus d'écrasement ; erreur réseau préservant les fichiers existants ; téléchargement simulé réussi avec deux instantanés distincts ; refus d'export si la licence courante n'est pas reconnue. Ces tests ne constituent pas une validation des données officielles ni du service distant.

## 8. Suite proposée, après validation

Depuis un terminal autorisé à accéder au portail, relancer :

```powershell
.\.venv\Scripts\python.exe -m src.odre_data download
```

Si le manifeste est `complete`, remplacer `odre_EXEMPLE` par le dossier réellement obtenu, puis :

```powershell
.\.venv\Scripts\python.exe -m src.odre_data audit data/raw/odre_EXEMPLE/observations.json --output reports/audit_observations.json
```

La sortie est refusée si le rapport existe déjà : choisir un nouveau nom. Examiner ensemble le manifeste et le rapport, résoudre les conventions de mesure, puis compléter le présent document avec des résultats réellement calculés. Ne pas commencer l'analyse exploratoire ou l'agrégation définitive avant validation.

Le protocole scientifique de la mission 005 n'est pas modifié. Aucun modèle, performance prédictive, commit ou push. Les données et manifestes bruts restent exclus par `.gitignore`.

## 9. Complément — Acquisition réussie et Mission 006 bis

Les sections précédentes décrivent l'état lors de la première exécution de la mission 006. Depuis, un instantané complet a été acquis dans `data/raw/odre_f6gejuyq/` et un audit produit dans `reports/audit_observations.json`. La mention initiale « aucune observation récupérée » ne décrit donc plus l'état actuel du projet ; elle est conservée comme historique.

Le 4 novembre 2026, l'export a été relu et son empreinte comparée au manifeste et au rapport initial : `65f6a751d0e02d1a11c6d5e85dc620734b04ffc19f2c2ed3acc110e828125cf3`. Tous les résultats descriptifs initiaux ont été recalculés et confirmés : 258 576 lignes, 12 colonnes, 33 occurrences temporelles excédentaires et 31 créneaux absents. Les 33 groupes contiennent chacun deux lignes ; 22 ont des puissances électriques contradictoires et aucun n'est intégralement identique.

Les 1 440 statuts RTE manquants couvrent exactement septembre 2026 local. Le flag vaut `non` sur toutes les lignes. Des divergences entre statuts annuels observés et description générale ont également été relevées. Les listes exhaustives, sources officielles, limites et propositions non appliquées sont dans [le diagnostic temporel](diagnostic_anomalies_temporelles.md). Les spécifications RTE documentent la puissance moyenne pour éCO2mix consolidé/définitif ; la filiation exacte et la convention début/fin d'intervalle du jeu ODRÉ restent à confirmer.

Le script local `src/diagnostic_temporel.py` permet de reproduire ce diagnostic. Les données brutes et le rapport JSON initial restent inchangés. Aucune correction, agrégation ou modélisation n'est appliquée.
