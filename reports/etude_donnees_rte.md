# Étude du jeu ODRÉ et protocole de prévision à 24 heures

> Note de suivi du 5 novembre 2026 : les propositions et vérifications impossibles ci-dessous décrivent l'étude documentaire initiale du 4 novembre 2026. L'acquisition et l'audit ont ensuite été réalisés et sont décrits dans [l'audit qualité](audit_qualite_donnees.md) et [le diagnostic temporel](diagnostic_anomalies_temporelles.md). La section 7 conserve les étapes alors proposées ; elle ne signifie pas que l'acquisition est toujours en attente. Les incertitudes physiques restent détaillées dans [l'étude d'agrégation](etude_agregation_horaire.md).

Mission 005 — M1 MIASHS 2026–2027. Consultation documentaire : 4 novembre 2026.

## 1. Portée et sources consultées

Cette étude utilise des pages de métadonnées et des extraits de schéma accessibles par l'outil de consultation web. Aucun export, fichier de données ou appel à un endpoint d'observations n'a été téléchargé ou exécuté. Aucun contrôle statistique sur les observations, entraînement ou résultat de performance n'a été réalisé.

Sources officielles effectivement consultées :

- **S1 — [Fiche ODRÉ](https://odre.opendatasoft.com/explore/dataset/consommation-quotidienne-brute/)** : description du produit et périmètres.
- **S2 — [Fiche ODRÉ en français](https://odre.opendatasoft.com/explore/dataset/consommation-quotidienne-brute/?flg=fr-fr)** : métadonnées détaillées et champs visibles dans les résultats de recherche ; l'ouverture directe renvoie une version plus ancienne et partiellement dynamique.
- **S3 — [Référencement officiel sur data.gouv.fr](https://www.data.gouv.fr/datasets/consommation-quotidienne-brute)** : producteurs, licence, ressources et statuts récents.
- **S4 — [Fiche ODRÉ en anglais](https://odre.opendatasoft.com/explore/dataset/consommation-quotidienne-brute/?flg=en-us)** : extraits de schéma consultés dans les résultats de recherche, notamment les identifiants des champs. Aucun exemple chiffré n'est utilisé comme résultat d'analyse.

Limites d'accès : l'endpoint de métadonnées `/api/explore/v2.1/catalog/datasets/consommation-quotidienne-brute` est inaccessible via l'outil web. Le lien Etalab de la licence redirige vers l'accueil de data.gouv.fr : le texte juridique n'a donc pas été vérifié. Ces limites ne sont pas contournées. Les ressources CSV/JSON proposées n'ont pas été ouvertes. Les vues indexées peuvent être décalées par rapport au portail courant.

## 2. Fiche du candidat : faits documentaires

| Élément | Constat et source |
|---|---|
| Produit | « Consommation quotidienne brute », identifiant `consommation-quotidienne-brute` (S1) |
| Production et diffusion | NaTran, RTE, Teréga ; diffusion ODRÉ. La série électrique est attribuée à RTE (S2–S4) |
| Électricité | `consommation_brute_electricite_rte` : MW, demi-heures ; `statut_rte` : statut (S2, S4) |
| Territoire électrique | France métropolitaine hors Corse, maille nationale (S1, S2) |
| Historique annoncé | 2012 à date (M−1) ; actualisation mensuelle (S2, extrait indexé) |
| Statuts récents | 2012–2024 définitifs ; 2025–2026 consolidés (S1, S3) |
| Temps | Métadonnée UTC ; champs `date_heure`, `date`, `heure` à confirmer dans le schéma courant (S2, S4) |
| Gaz | Horaire, MW PCS 0 °C ; champs NaTran, Teréga, total gaz et statuts associés (S1, S4) |
| Autres champs | `consommation_brute_totale`, `flag_ignore` : ne pas les employer comme cible électrique (S4) |
| Accès et licence | Consultation publique ; exports CSV/JSON et API annoncés ; Licence Ouverte v2.0 indiquée (S2, S3) |

La date minimale et la date maximale exactes des observations ne sont pas vérifiées. Ne pas confondre profondeur annoncée, date de traitement du portail et couverture effective. Une ancienne vue S2 indique d'autres statuts : retenir provisoirement S1/S3, puis vérifier à l'acquisition. Les modalités techniques d'API, quotas et conditions détaillées de réutilisation restent à confirmer.

## 3. Adéquation et décision proposée

**Avis : candidat adapté sous conditions pour une étude rétrospective nationale horaire, insuffisant seul pour démontrer une prévision opérationnelle en temps réel.**

Le pas électrique est compatible avec une agrégation horaire et l'historique annoncé permet d'envisager plusieurs cycles annuels. Cela ne démontre ni la complétude ni la qualité des valeurs. Le titre « quotidienne » ne signifie pas qu'il s'agit uniquement de totaux journaliers.

La mise à jour mensuelle annoncée empêche de supposer que la consommation des dernières heures est disponible sur ce portail à l'instant d'une prévision. Utiliser les valeurs révisées de l'archive comme si elles avaient été connues immédiatement introduirait une hypothèse rétrospective forte. Pour un usage opérationnel, il faudra identifier une source à faible délai et des versions historiques publiées, ou adapter les variables au délai réellement établi.

Le sujet devra préciser « France métropolitaine hors Corse ». Ne pas extrapoler les conclusions aux territoires absents. Écarter les séries gazières du premier protocole : elles ont une autre fréquence et une autre définition physique. Le total multi-énergies n'est pas une mesure de consommation électrique.

## 4. Cible, horodatage et agrégation

### Définition proposée

Choisir une origine quotidienne fixe **T = 00:00 UTC**, produisant 24 valeurs horaires pour les intervalles `[T, T+1 h)`, …, `[T+23 h, T+24 h)`. Ce sont 24 heures écoulées ; ce n'est pas nécessairement le jour civil français suivant. Conserver cette convention identique pour les modèles et les références naïves.

Définir `y_s` comme la puissance électrique moyenne, en MW, sur `[s, s+1 h)`. La cible est le vecteur `(y_T, …, y_{T+23 h})`. La dernière heure théoriquement complète à T est `[T−1 h, T)`, mais sa disponibilité effective dépend du délai de publication.

### Passage de 30 minutes à une heure

Sous réserve que les mesures soient des puissances moyennes demi-horaires et que leur horodatage désigne le début d'intervalle :

`y_s = (P_s + P_{s+30 min}) / 2`.

La moyenne reste en MW ; la somme directe des deux puissances n'est pas la cible. L'énergie sur l'heure vaut `0,5 × P_s + 0,5 × P_{s+30 min}` MWh. Si les mesures sont instantanées, cette moyenne est une approximation à expliciter, pas une énergie mesurée exacte.

La signification début/fin d'intervalle et moyenne/instantané n'a pas été établie dans les métadonnées consultées. La confirmer avant tout calcul ; si l'étiquette marque une fin d'intervalle, ajuster les bornes avant agrégation.

Exiger deux demi-heures uniques et valides par heure. Marquer une heure incomplète comme manquante, sans extrapoler automatiquement une seule valeur. Contrôler doublons, ordre, trous, unités et statuts ; ne pas remplacer un manquant par zéro. Les règles de qualité seront définies avant l'évaluation, sans suppression a posteriori des erreurs difficiles.

### Fuseaux et changements d'heure

Parser `date_heure` comme date consciente du fuseau, vérifier ses offsets et travailler sur une grille UTC régulière. Dériver les variables calendaires avec `Europe/Paris`. Ne pas reconstruire l'index à partir de chaînes locales `date` et `heure` sans désambiguïsation.

La journée civile locale peut comporter 23 ou 25 heures : conserver les deux occurrences d'une heure répétée, avec leur offset ; ne pas inventer une heure absente. Une fenêtre de 24 heures UTC conserve toujours 24 cibles. La définition alternative « jour civil suivant en France » aurait une longueur variable et constituerait un autre protocole à valider.

## 5. Informations disponibles et variables explicatives

Toutes les variables d'une origine T doivent être connues ou publiées au plus tard à T. Distinguer date de mesure, date de publication et date de révision. Tenir une table de disponibilité ; les statuts de qualité servent à l'audit et ne doivent pas devenir des prédicteurs révélant une révision future.

### Consommation passée

Proposer la dernière fenêtre de 24 heures, des retards quotidiens et hebdomadaires, et des statistiques sur 24 heures et 7 jours. Pour chaque cible `y_s`, les références `y_{s−24 h}` et `y_{s−168 h}` sont utilisables seulement si publiées à T. Toutes les fenêtres glissantes se terminent avant l'origine et respectent le délai de publication, sans centrage.

Pour commencer, comparer des modèles directs par horizon : régression linéaire, Random Forest et Gradient Boosting. Les 24 modèles éventuels utilisent le même ensemble d'informations arrêté à T ; jamais la vraie consommation des premières heures futures pour prédire les suivantes. Le choix multi-sorties ou direct sera arrêté en validation, sans multiplier les recherches sur le test.

### Calendrier

Heure locale cible, jour de semaine, week-end, mois/saison, encodages cycliques et indicateur de changement d'heure. Les jours fériés sont envisageables après choix d'un calendrier officiel pertinent pour le périmètre national ; les vacances scolaires exigent une gestion des zones. Ces sources ne sont pas vérifiées dans cette mission. Les variables calendaires futures déterministes peuvent être connues à T.

### Météorologie : option conditionnelle

Ne pas intégrer la météo au protocole initial : aucune source, archive de prévisions ou licence météorologique n'a été vérifiée ici. Une extension pourrait utiliser des températures passées effectivement disponibles et des prévisions de température émises au plus tard à T, avec stations et pondérations territoriales documentées.

Exiger pour chaque prévision météo une date d'émission, une échéance et la disponibilité historique des versions. Des observations futures ou réanalyses ne peuvent pas représenter des prévisions disponibles à T. Une étude utilisant la météo réellement observée serait un scénario oracle séparé, explicitement non opérationnel.

## 6. Évaluation chronologique proposée

### Découpage

Après contrôle de la couverture, réserver la dernière année civile complète et suffisamment documentée comme test, l'année précédente comme validation, et les années antérieures comme entraînement. Si 2012–2024 est complet et exploitable, un scénario candidat est : entraînement 2012–2022, validation 2023, test 2024. Ce scénario est une proposition, pas un constat sur les données. Garder les années consolidées ultérieures pour une analyse complémentaire seulement après décision documentée.

En validation, utiliser plusieurs fenêtres chronologiques à entraînement croissant pour examiner la stabilité saisonnière. Fixer les hyperparamètres et les règles de préparation avant d'ouvrir le test. Un éventuel réentraînement sur entraînement + validation précède une unique évaluation finale ; ses choix ne sont pas révisés après consultation du test.

Attribuer les exemples par leurs 24 cibles : aucune cible d'entraînement ne doit franchir la frontière de validation, ni une cible de validation celle du test. Les historiques antérieurs peuvent servir de contexte au début d'un bloc ; les cibles futures de ce bloc ne servent jamais à ajuster le modèle à l'avance. Un réentraînement glissant éventuel doit suivre un calendrier fixé et attendre la disponibilité des labels.

### Références naïves

- Référence principale saisonnière hebdomadaire : `prévision(y_s) = y_{s−168 h}`.
- Référence complémentaire quotidienne : `prévision(y_s) = y_{s−24 h}`.

Ces références utilisent des retards de durée en UTC. Leur heure locale peut différer au changement d'heure : le signaler et analyser ces journées séparément. Une référence à heure locale identique exige une règle explicite pour les heures ambiguës ou absentes. Toutes les méthodes sont évaluées sur les mêmes origines et cibles valides ; publier le nombre et le motif des exclusions.

### Métriques

Pour les N erreurs horaires `e_i = prévision_i − observation_i` :

- `MAE = somme(|e_i|) / N`, en MW ;
- `RMSE = racine(somme(e_i²) / N)`, en MW.

Présenter les scores globaux sur les couples origine/horizon, les scores par horizon 1 à 24, par saison et sur les périodes de changement d'heure. La RMSE accentue les grandes erreurs. Ne pas confondre ces métriques de puissance avec des erreurs d'énergie. Aucun score n'est calculé dans cette mission.

### Prévention des fuites

- Aucun mélange aléatoire des observations temporelles.
- Ajuster imputation, standardisation, sélection de variables et hyperparamètres exclusivement sur les blocs d'entraînement correspondants.
- Interdire l'interpolation utilisant le futur pour les variables disponibles à T ; ne pas imputer les cibles du test pour calculer les scores.
- Calculer les variables par origine, pas à partir d'une série complète incluant les cibles futures.
- Ne pas employer de météo observée future, de statut final futur ou de données révisées sans signaler l'hypothèse.
- Distinguer explicitement performance rétrospective sur archive révisée et performance opérationnelle reproductible avec les publications de l'époque.

## 7. Questions ouvertes et étapes soumises à validation

1. Confirmer l'accord sur 24 heures UTC et une origine à 00:00 UTC, plutôt qu'un jour civil français.
2. Confirmer la cible : puissance moyenne horaire électrique, France métropolitaine hors Corse.
3. Vérifier avant acquisition la convention d'horodatage, la nature des puissances, les bornes exactes, les champs et les statuts courants, ainsi que `flag_ignore`.
4. Établir le délai réel de publication et l'existence de versions historiques ; sinon annoncer une étude rétrospective avec disponibilité idéale supposée des consommations passées.
5. Vérifier les conditions détaillées de licence, l'attribution requise et les modalités d'API avant réutilisation.
6. Après autorisation distincte d'acquisition, auditer couverture, manquants, doublons, valeurs suspectes et stabilité de définition ; arrêter alors les dates des blocs.
7. Reporter la météo jusqu'à justification de sa disponibilité à l'origine.

## 8. Contrôles de la mission

Avant rédaction : dépôt propre sur `main`, suivi local `origin/main`, dernier commit local `b219a1e` ; lecture de `AGENTS.md`, du README et inventaire des fichiers. Le statut local ne constitue pas une interrogation distante de GitHub.

Seul ce document est ajouté. `requirements.txt` n'est pas modifié. Aucun téléchargement d'observations, notebook, modèle, commit ou push n'est réalisé. Les constats documentaires ne remplacent pas une validation effective des données.
