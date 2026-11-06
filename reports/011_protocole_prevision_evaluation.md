# Protocole scientifique de prévision électrique à 24 heures — Mission 011

Date de rédaction : 6 novembre 2026. Projet M1 MIASHS 2026–2027. Référence locale initiale : branche `main`, commit `61ff343`, répertoire de travail propre.

**Statut : propositions méthodologiques soumises à examen scientifique.** Ce document ne sélectionne pas une convention physique, ne construit pas de variables et ne rapporte aucune performance prédictive. Les dates, références et règles proposées ne constituent pas des décisions définitivement approuvées.

## 1. Base documentaire et niveaux de preuve

L'étude repose exclusivement sur les fichiers locaux suivants ; aucune source distante n'est interrogée pendant cette mission.

| Référence | Fichier et contribution |
| --- | --- |
| R1 | [README](../README.md) : périmètre national hors Corse, objectifs et état du projet |
| R2 | [Étude initiale](etude_donnees_rte.md), sections 3–6 : disponibilité, origine UTC, premières propositions d'évaluation |
| R3 | [Étude d'agrégation](etude_agregation_horaire.md), sections 2–7 : preuves physiques insuffisantes, supports, scénarios et risques temporels |
| R4 | [Préparation horaire expérimentale](preparation_horaire_experimentale.md) : formules A/B, bornes, statuts, provenance et empreintes |
| R5 | [Synthèse exploratoire](010_synthese_exploratoire.md) et [notebook exécuté](../notebooks/010_analyse_exploratoire.ipynb) : couverture, populations et profils descriptifs |
| R6 | [Audit qualité](audit_qualite_donnees.md), [audit des observations](audit_observations.json) et [diagnostic temporel](diagnostic_anomalies_temporelles.md) : anomalies et limites de l'instantané |

La source officielle demeure [ODRÉ — Consommation quotidienne brute](https://odre.opendatasoft.com/explore/dataset/consommation-quotidienne-brute/). Cette URL est rappelée pour la provenance, sans nouvelle vérification des métadonnées. Les attributions RTE/ODRÉ et la Licence Ouverte 2.0 restent documentées dans les rapports d'acquisition.

Trois niveaux sont distingués dans la suite : **fait documenté** dans les rapports existants, **proposition** pour une future expérience, **question ouverte** exigeant une preuve ou une décision supplémentaire. Les chiffres repris ne sont pas présentés comme de nouveaux calculs sur les observations.

### 1.1 Faits documentés

- L'instantané acquis le 4 novembre 2026 contient 258 576 observations brutes. La grille demi-horaire comporte 258 574 créneaux, dont 22 ambigus et 31 absents ; les doublons de même puissance sont conservés avec provenance.
- Chaque CSV horaire comporte 129 286 lignes, de l'heure commençant le `2011-12-31T23:00:00+00:00` à celle commençant le `2026-09-30T20:00:00+00:00`. Le dernier intervalle se termine à `2026-09-30T21:00:00+00:00`.
- Les puissances calculables sont au nombre de 129 251 pour A et 129 233 pour B. Les admissibilités strictes sont respectivement 128 532 et 128 499 ; leur intersection compte 128 493 heures, avec 793 exclusions de la grille commune (R4–R5).
- Le strict est une admissibilité technique sous hypothèse : deux composantes présentes et résolues, statuts connus et homogènes dans `{Définitif, Consolidé}`, absence de discordance calendaire. Ce n'est pas une certification physique. Les flags ne sont pas interprétés comme filtres.
- Les 1 440 statuts RTE absents concernent septembre 2026 selon le diagnostic. Aucun statut ni consommation n'est remplacé.
- L'EDA retrouve des profils saisonniers, hebdomadaires et horaires dans les deux scénarios. Elle a exploré l'ensemble de la période disponible, y compris les années susceptibles de devenir des blocs d'évaluation.

### 1.2 Questions non résolues

La nature moyenne ou instantanée du champ, le rattachement exact des étiquettes, leur stabilité historique, l'explication des anomalies et les dates de publication/révision restent insuffisamment établis pour cet export. Les statuts actuels ne reconstituent pas leurs versions historiques. Aucune donnée météorologique ni archive de prévisions météorologiques n'est disponible dans le périmètre étudié.

## 2. Cible, origine et horizons

### 2.1 Grandeur physique souhaitée et cibles expérimentales

La grandeur visée est la puissance électrique moyenne horaire nationale hors Corse, en MW. Si `p(u)` désigne la puissance physique et `Δ = 1 h`, sa définition serait :

\[
Y_h = \frac{1}{\Delta}\int_h^{h+\Delta}p(u)\,du.
\]

L'intégrale est une énergie en MWh ; la division par la durée restitue des MW. L'égalité de cette grandeur avec les CSV n'est pas démontrée : elle suppose notamment des moyennes demi-horaires correctement alignées.

En notant `P_r` la puissance portant l'étiquette source `r`, les cibles statistiques actuellement disponibles sont :

\[
Y_h^A=(P_h+P_{h+\Delta/2})/2,\qquad
Y_h^B=(P_{h+\Delta/2}+P_{h+\Delta})/2.
\]

Ces formules ne sont définies que pour les composantes résolues et présentes. Sous A, une étiquette marque hypothétiquement un début de demi-heure ; sous B, une fin. Les deux sorties sont étiquetées par `hour_start_utc = h`, pour l'intervalle supposé `[h,h+Δ)`. B n'est donc pas obtenu par simple renommage d'une ligne A : les paires diffèrent. Aucun déplacement destiné à améliorer un score ou la continuité n'est admissible.

**Proposition :** conduire deux expériences symétriques, identiques quant aux origines, dates et budgets de comparaison, avec des cibles distinctes `Y^A` et `Y^B`. Les résultats seraient conditionnels à chaque hypothèse ; un meilleur score ne résoudrait pas la convention physique.

### 2.2 Convention principale proposée

Retenir une émission quotidienne à **t = 00:00 UTC**, immédiatement avant le premier intervalle cible. Pour `k = 1,…,24` :

\[
h(t,k)=t+(k-1)\Delta,\qquad
Y_{t,k}^{s}=Y_{h(t,k)}^{s},\quad s\in\{A,B\}.
\]

| Horizon | Intervalle cible UTC | Signification |
| --- | --- | --- |
| H+1 | `[t,t+1 h)` | Première heure à venir, achevée à t+1 h |
| H+k | `[t+(k−1) h,t+k h)` | Puissance de l'intervalle, pas une mesure ponctuelle à t+k |
| H+24 | `[t+23 h,t+24 h)` | Dernière heure de la fenêtre |

Cette convention prolonge R2 et R3 : 24 sorties fixes, temps UTC non ambigu et mêmes instants pour toutes les méthodes. L'origine est quotidienne ; « glissante » désigne ici une fenêtre future redéfinie à chaque émission quotidienne, **pas une émission toutes les heures**. Une émission horaire serait une extension distincte, avec cibles répétées entre origines et pondérations à expliciter.

La convention principale correspond aux **24 prochaines heures écoulées**, pas au lendemain civil français. À 00:00 UTC, l'heure locale est 01:00 ou 02:00 selon la saison. Le choix est pratique pour le protocole, sans prétendre représenter un horaire réglementaire ou une pratique RTE vérifiée.

### 2.3 Alternative du lendemain civil et changements d'heure

Une prévision du lendemain civil pourrait être émise à midi local du jour D pour `[minuit de D+1,minuit de D+2)` en `Europe/Paris`. Convertir séparément les deux minuits en UTC : la fenêtre comporte 23, 24 ou 25 heures physiques. Elle n'a ni la même origine ni les mêmes horizons que la proposition principale.

Dans le protocole principal, les 24 intervalles UTC demeurent distincts aux transitions. Les calendriers explicatifs sont dérivés des instants UTC avec `Europe/Paris`, en conservant les offsets et l'identité UTC des heures répétées. Aucune heure locale absente n'est créée, aucune occurrence répétée n'est fusionnée. Une fenêtre UTC peut chevaucher deux dates locales. Les anomalies réelles des sources restent des anomalies et ne sont pas justifiées par le seul changement d'heure.

## 3. Informations disponibles à l'émission

### 3.1 Temps de mesure, publication et révision

Pour chaque valeur et chaque version, distinguer : étiquette d'observation, support temporel supposé, fin du support, première publication, révisions, téléchargement et version effectivement accessible. Une valeur finale téléchargée en novembre 2026 n'est pas une preuve de disponibilité en 2018.

Noter `a(v)` l'instant réel de disponibilité de la version `v`. L'ensemble d'information admissible à t est constitué des seules versions avec `a(v) ≤ t`. Pour une consommation historique utilisée comme prédicteur, exiger en plus un support achevé au plus tard à t. Le statut final et les motifs de qualité constatés rétrospectivement ne sont pas automatiquement connus à l'émission.

Un support qui se termine exactement à t satisfait la condition temporelle d'achèvement, mais sa valeur n'est pas nécessairement publiée à cet instant. La disponibilité à l'émission doit être démontrée séparément, même si aucun support futur n'est utilisé. Cette distinction s'applique notamment à la référence quotidienne à H+24.

L'archive actuelle ne fournit pas un journal suffisant pour reconstruire `a(v)`. L'actualisation mensuelle décrite dans R2 ne donne ni une disponibilité immédiate ni un délai exact constant. Retarder arbitrairement les consommations d'un jour ou d'une semaine ne prouve donc pas leur disponibilité réelle.

### 3.2 Tableau de disponibilité et risques

| Famille | Proposition conditionnelle | Disponibilité exigée à t | Risque et prévention |
| --- | --- | --- | --- |
| Consommation historique | Heures passées résolues, même scénario que la cible | Fin des supports et publication des versions avant t | Archive révisée assimilée au temps réel ; conserver versions et hypothèse d'accès |
| Retards relatifs à l'origine | `Y^s_{t−jΔ}`, j entier positif | Heure achevée et valeur publiée à t | `j=1` ne suffit pas si publication retardée ; pas de retard choisi selon une couverture future |
| Retards relatifs à la cible | `Y^s_{h(t,k)−dΔ}` | Dépend de k et du délai, pas du seul nombre d'heures de retard | Un retard positif peut encore pointer après t ; contrôler chaque support |
| Statistiques glissantes | Moyenne, dispersion ou autre résumé d'un historique autorisé | Toutes les composantes et leurs versions disponibles à t | Fenêtre centrée, remplissage futur ou calcul sur toute la série ; bornes arrêtées avant le seuil d'accès |
| Calendrier déterministe | Heure/jour/mois/saison des intervalles futurs et calendrier UTC/local | Calculable à t à partir de règles de fuseau documentées | Heure locale ambiguë ; conserver UTC et offset ; aucune consommation future dans le calcul |
| Jours fériés et vacances | Extension éventuelle avec calendrier territorial documenté | Calendrier publié à t, source et périmètre vérifiés | Lundi–vendredi n'est pas un indicateur exact de jour ouvré ; sources absentes actuellement |
| Statuts, flags, anomalies | Audit des cibles et des historiques ; aucun prédicteur par défaut | Version de l'indicateur connue à t si usage explicatif | Statut final révélant une révision ; distinguer masque rétrospectif et information opérationnelle |
| Météorologie | Exclue du protocole initial | Pour une extension : prévision archivée avec émission et diffusion avant t, échéance, zone et licence | Température future observée ou réanalyse utilisée comme prévision ; aucune disponibilité démontrée ici |
| Transformations et profils estimés | Ajustement ultérieur sur l'entraînement de chaque pli uniquement | Paramètres ajustés avec données et labels admissibles avant la coupure d'ajustement | Standardisation, sélection, climatologie ou imputation ajustées sur validation/test |

Les listes de retards et tailles de fenêtres seront précisées lors d'une mission ultérieure. Une statistique ayant une composante absente est indisponible selon la politique initiale proposée ; pas de moyenne sur une fenêtre raccourcie sans règle distincte. Aucune imputation de cible n'est proposée.

### 3.3 Deux niveaux d'expérience à ne pas confondre

1. **Étude rétrospective conditionnelle sur archive révisée — première expérience recommandée** : ce benchmark académique est recommandé pour commencer, sous une hypothèse explicite d'accès aux valeurs finales passées. Il ne constitue pas une simulation opérationnelle historiquement vérifiée. Même si tous les supports sont achevés au plus tard à t, les dates réelles de publication et les versions alors disponibles ne sont pas reconstituées. L'hypothèse d'accès et les limites relatives aux révisions doivent accompagner chaque tableau de scores.
2. **Évaluation compatible avec les publications de l'époque** : exige des versions horodatées, des délais démontrés et un accès historique reconstituable, y compris pour les labels d'entraînement. Elle n'est pas actuellement justifiée par le seul instantané.

Un paramètre de délai `L ≥ 0` peut servir à une **analyse de sensibilité proposée**, en n'utilisant que des heures achevées avant `t−L`. Il s'agit d'un complément méthodologique à faire examiner, non d'une estimation du vrai délai ODRÉ. `L=0` serait une hypothèse idéale, non une disponibilité vérifiée. Aucun L n'est fixé ou appliqué ici.

À chaque ajustement futur daté `f`, les labels utilisés doivent aussi avoir été publiés avant f pour une interprétation opérationnelle. Un simple découpage par date d'observation ne résout pas le problème des révisions.

## 4. Découpage chronologique proposé

### 4.1 Blocs principaux

Utiliser des bornes UTC semi-ouvertes pour les **supports des cibles**, indépendamment des années civiles locales utilisées dans certains profils de l'EDA.

| Usage proposé | Supports cibles UTC | Justification et limite |
| --- | --- | --- |
| Entraînement initial | `[2012-01-01T00:00Z,2023-01-01T00:00Z)` | Historique long, plusieurs cycles annuels et régimes de consommation ; besoin de contrôler leur stabilité |
| Validation et choix méthodologiques | `[2023-01-01T00:00Z,2025-01-01T00:00Z)` | Deux cycles annuels pour examiner la stabilité et limiter les choix sur une seule année |
| Test rétrospectif principal | `[2025-01-01T00:00Z,2026-01-01T00:00Z)` | Dernière année entière couverte temporellement par l'instantané ; consolidation et qualité à conserver explicitement |
| Évaluation complémentaire ultérieure | Partie disponible de 2026 | Année incomplète, statuts absents en septembre et bord final incomplet ; pas de comparaison annuelle brute avec 2025 |

« Année entière couverte » ne signifie pas que toutes ses cibles sont strictes. Les effectifs de fenêtres réellement admissibles par bloc devront être calculés ultérieurement. La première heure locale de 2012 disponible avant `2012-01-01T00:00Z` peut seulement servir de contexte, sous condition d'accès ; elle n'est pas une cible de ce découpage.

R2 proposait conditionnellement 2012–2022 / 2023 / 2024 avant la connaissance de la couverture effective. **La présente proposition change ce découpage** : la couverture jusqu'en 2026 et l'EDA sur 2012–2025 permettent de proposer deux années de validation et 2025 comme test. Ce changement n'est pas une décision appliquée. Il n'est fondé sur aucun score prédictif. Le statut consolidé possible de 2025 interdit de l'assimiler à une vérité immuable ou à des versions connues en temps réel.

### 4.2 Attribution des fenêtres et frontières

Un exemple appartient à un bloc `[b,e)` seulement si ses **24 intervalles cibles entiers** sont inclus dans ce bloc : `t ≥ b` et `t+24 h ≤ e`. Aucune cible d'entraînement ne doit déborder sur validation ; aucune cible utilisée pour les choix ne doit déborder sur le test. Les dates d'origine seules ne suffisent pas à cette vérification.

Avec l'émission quotidienne UTC proposée et les frontières à minuit UTC, les fenêtres successives de 24 heures ne se chevauchent pas. Si l'émission devenait horaire, il faudrait purger les exemples dont les cibles franchissent une frontière, contrôler les cibles répétées et leur pondération ; ce n'est pas implémenté ici. Aucun embargo supplémentaire arbitraire n'est fixé : une séparation additionnelle dépendrait des supports, délais et procédures d'ajustement.

Les historiques précédant un bloc peuvent fournir le contexte des premières origines sans être des cibles de ce bloc. En cours de validation/test, les consommations antérieures du même bloc peuvent devenir des entrées à une origine ultérieure **si elles sont alors disponibles**, sans réajuster les paramètres du modèle. Cela ne permet jamais d'injecter la vraie consommation de H+1 dans la prévision H+2 émise au même t.

Les premiers exemples sans profondeur historique suffisante sont exclus ou déclarés non émissibles selon une règle fixée avant les scores ; aucune valeur n'est inventée. Ne pas mélanger aléatoirement les origines ou les observations horaires.

### 4.3 Validation à origine glissante et ajustement final

Proposer deux plis à entraînement croissant : apprentissage jusqu'à fin 2022 puis validation en 2023 ; apprentissage jusqu'à fin 2023 puis validation en 2024. Dans le second pli, les données 2023 ne peuvent être assimilées à des labels disponibles pour une simulation opérationnelle sans vérifier leur publication à la date d'ajustement.

L'émission des prévisions se déplace chaque jour ; cela ne signifie pas réentraîner chaque jour. Pour une première comparaison contrôlée, proposer des paramètres fixes dans chaque année de validation. Un calendrier de réentraînement plus fréquent serait une expérience séparée, fixée à l'avance et conditionnée à la disponibilité des labels.

Après les choix sur les plis, une future procédure pourrait réajuster sur 2012–2024 puis évaluer 2025 sans modifier les choix à partir des erreurs du test. Prétraitements, sélection, hyperparamètres et éventuels profils estimés doivent être réajustés uniquement sur les données admissibles de chaque entraînement. Aucun ajustement n'est effectué pendant cette mission.

### 4.4 Limite du test déjà exploré

L'EDA a porté sur toute la période, dont 2025 et 2026. Le test proposé n'est donc **pas une confirmation entièrement indépendante d'une période jamais examinée**. Il reste utile comme évaluation chronologique rétrospective à condition de documenter cette exposition et de geler les choix avant les scores. Une confirmation prospective exigerait ultérieurement des observations nouvelles non explorées et un protocole enregistré avant leur analyse ; aucune acquisition n'est prévue ici.

## 5. Références simples proposées

Ces références sont définies sans produire de prévisions. Elles s'appliquent séparément à A et B, sur les mêmes origines et avec les mêmes règles d'accès que les futurs modèles.

Pour une référence relative à la cible de retard d heures, le support de `Y^s_{h(t,k)−dΔ}` se termine à `t+(k−d)Δ`. Sous un seuil d'accès hypothétique `t−L`, une condition nécessaire est :

\[
d\Delta \ge k\Delta+L.
\]

Cette inégalité ne remplace pas la preuve de publication et de version. Elle empêche d'utiliser un support futur comme historique.

| Référence | Définition proposée pour H+k | Conditions et limites |
| --- | --- | --- |
| Persistance | Dernière puissance admissible publiée à t, répétée pour les 24 horizons | Chercher uniquement dans le passé accessible ; conserver son âge. Si aucune valeur n'existe, prévision indisponible. Un âge maximal admissible reste à fixer ; pas de repli silencieux |
| Jour précédent en durée UTC | `Y^s_{h(t,k)−24 h}` | Pour H+24, l'heure de référence finit exactement à t, sans garantie de publication à cet instant. Son usage suppose un accès sans délai dans le benchmark idéal ; en simulation opérationnelle, sa disponibilité doit être démontrée. Un délai positif peut rendre certains horizons non émissibles |
| Semaine précédente en durée UTC | `Y^s_{h(t,k)−168 h}` | Pour H+24, la référence finit à t−144 h ; délai et versions doivent encore être vérifiés. Sept jours de recul ne garantissent pas l'accès sur un portail mensuel |
| Combinaison quotidienne/hebdomadaire | Moyenne à poids fixes 1/2 des deux références précédentes | Motivations exploratoires : cycles quotidiens et hebdomadaires (R5). Nécessite les deux valeurs ; aucune substitution si l'une manque. Complément méthodologique proposé, sans garantie d'amélioration |

Les références à 24 h et 168 h UTC sont des traductions simples de « même heure du jour/de la semaine précédente », mais **ne conservent pas toujours la même heure locale** aux changements d'heure. Une variante strictement locale serait distincte : construire la date locale précédente, rechercher l'heure locale identique et conserver l'identité UTC. Si cette heure est absente ou correspond à deux occurrences, déclarer la référence indisponible tant qu'une règle explicite n'est pas retenue ; ne choisir ni fusionner automatiquement les occurrences. Comparer ensuite sa couverture à celle de la référence UTC.

Une référence indisponible reste indisponible ; aucun recours caché à une consommation future, aucun chaînage avec les véritables premières cibles. Les valeurs extrêmes de l'EDA ne sont pas supprimées pour faciliter une référence ou améliorer une métrique.

## 6. Qualité, masques et populations d'évaluation

Proposer le strict hérité de R4 comme qualité principale de cible ; les motifs d'exclusion et références sources demeurent conservés. Une analyse secondaire sur les puissances calculables, si retenue, reste séparée et ne remplace pas les cibles strictes absentes.

Pour une comparaison A/B, construire le masque de cible `q(t,k)` exigeant une cible stricte dans **les deux** scénarios au même intervalle UTC. Ce masque décrit la qualité rétrospective des labels ; il n'est ni un prédicteur ni une promesse de connaissance à l'émission. Les 128 493 heures communes de l'EDA ne donnent pas directement le nombre d'origines complètes : celles-ci dépendent du découpage, des 24 cibles et des historiques requis.

**Proposition principale :** utiliser des origines dont les 24 cibles sont strictes dans les deux scénarios et dont les entrées nécessaires au panel de méthodes sont admissibles selon la même hypothèse d'accès. Définir ce panel et les règles avant les scores. Une indisponibilité d'entrée ne doit pas disparaître silencieusement : publier les effectifs et causes, par méthode et par scénario, ainsi que la couverture du panel commun.

Le panel commun doit être défini **avant l'évaluation**, en distinguant deux niveaux :

- **Panel minimal de comparaison principale** : fixer la liste des méthodes et références de base ainsi que leurs besoins historiques indispensables. Leur population commune est déterminée par ces seuls besoins et par la qualité des cibles, sous la même hypothèse d'accès. Sa composition exacte reste à préciser avant toute évaluation.
- **Comparaisons complémentaires** : les méthodes ou références exigeant des historiques supplémentaires, par exemple une fenêtre plus longue que celles du panel minimal, sont comparées sur une population commune complémentaire définie à l'avance. Les méthodes du panel minimal y sont aussi évaluées pour permettre une comparaison à population identique. Ces exigences supplémentaires ne réduisent pas rétroactivement la population principale ; les deux couvertures et leurs exclusions sont publiées séparément.

Une prédiction absente ou non finie sur une origine préalablement admissible est un échec d'émission à signaler. Ne pas réduire après coup le masque selon les erreurs ou les sorties réussies de chaque méthode. Si une nouvelle famille de variables réduit la couverture, conserver l'évaluation du panel initial et ajouter une comparaison distincte sur une population explicitement annoncée.

**Analyse secondaire proposée :** scores par couples origine/horizon avec cible disponible, en précisant que les effectifs peuvent différer selon k et que la population ne coïncide plus avec celle des fenêtres complètes. Présenter aussi les masques propres de A et B comme sensibilité, sans attribuer à la convention seule les différences dues aux exclusions.

Les exclusions sont décomptées par bloc, année, saison, horizon, transition d'heure et motif ; distinguer manque de cible, manque d'historique, délai non établi et échec technique. Les masques et versions de règles doivent être archivés avant l'évaluation. Pas d'imputation de cible, de zéro à la place d'un absent, de correction automatique d'ambiguïté ou de suppression a posteriori d'un extrême.

## 7. MAE, RMSE et agrégation des 24 horizons

Pour un scénario s, une méthode m et un ensemble admissible `E_k` d'origines à l'horizon k, poser :

\[
e_{t,k}^{s,m}=\widehat Y_{t,k}^{s,m}-Y_{t,k}^{s},\qquad N_k=|E_k|.
\]

\[
\operatorname{MAE}_k=\frac{1}{N_k}\sum_{t\in E_k}|e_{t,k}|,
\qquad
\operatorname{RMSE}_k=\sqrt{\frac{1}{N_k}\sum_{t\in E_k}e_{t,k}^2}.
\]

Les deux métriques s'expriment en **MW**. La MAE représente l'amplitude absolue moyenne de l'erreur ; la RMSE donne davantage de poids aux grandes erreurs. Aucune ne décrit à elle seule le biais signé, et aucune n'est une erreur d'énergie ou un pourcentage.

En notant `E = {(t,k): t ∈ E_k, k=1,…,24}` et `N = Σ_k N_k`, les agrégations par couples sont :

\[
\operatorname{MAE}_{\rm globale}=\frac{1}{N}\sum_{k=1}^{24}\sum_{t\in E_k}|e_{t,k}|,
\quad
\operatorname{RMSE}_{\rm globale}=\sqrt{\frac{1}{N}\sum_{k=1}^{24}\sum_{t\in E_k}e_{t,k}^2}.
\]

Pour les fenêtres complètes proposées, les 24 horizons ont le même effectif : la MAE globale égale la moyenne des 24 MAE, mais la RMSE globale est la racine de la moyenne des **carrés** des 24 RMSE, pas la moyenne arithmétique de ces RMSE.

Si les effectifs diffèrent dans l'analyse secondaire, l'agrégation par couples pondère les horizons par `N_k`. Une présentation à poids égaux entre horizons peut être ajoutée : `MAE_macro = (1/24)Σ MAE_k` et `RMSE_macro = sqrt((1/24)Σ RMSE_k²)`. L'annoncer comme agrégation distincte. Si un effectif est nul, indiquer une métrique non définie et son effectif ; ne pas remplacer par zéro ni calculer silencieusement sur moins de 24 horizons.

Présenter séparément les résultats de A et de B, avec N, nombres d'origines, couverture et exclusions ; ne pas moyenner les deux cibles ou leurs scores pour masquer l'incertitude physique. Les comparaisons modèle/références portent sur les mêmes couples admissibles. Les ventilations saisonnières utilisent un calendrier local documenté ; les horizons restent UTC. Toute ventilation complémentaire conserve son effectif et ne conduit pas à sélectionner un scénario physique.

Les fenêtres quotidiennes non chevauchantes ne garantissent pas l'indépendance des erreurs : persistance temporelle et cycles restent possibles. Aucun test de significativité ni intervalle de confiance n'est proposé implicitement à partir d'hypothèses d'indépendance non établies. **Aucune métrique prédictive n'est calculée dans cette mission.**

## 8. Reproductibilité et décisions à examiner

Avant une implémentation ultérieure, conserver une configuration versionnée indiquant : origines et horizons, bornes UTC, scénario, politique de qualité, hypothèse de disponibilité et délai éventuel, références, règles d'historiques, panel comparé, masques, plis et protocole d'ajustement. Relier chaque expérience aux empreintes du brut, de la grille et du CSV concerné dans R4–R5, à la version du code et aux versions réellement observées de Python, dépendances et base des fuseaux. Un fichier de dépendances non figées ne garantit pas une reproduction identique (voir [l'environnement](environnement.md)).

| Sujet | Proposition | Point restant ouvert |
| --- | --- | --- |
| Cible et émission | 24 intervalles horaires, émission quotidienne 00:00 UTC, H+1 achevé à t+1 h | Accord sur cette fenêtre plutôt que le lendemain civil |
| Convention physique | Deux expériences A/B symétriques | Nature et supports des mesures, stabilité historique |
| Accès aux consommations | Distinguer benchmark idéal sur archive et simulation avec publications | Versions et délais réels ; faisabilité des retards quotidiens/hebdomadaires |
| Découpage | 2012–2022 entraînement, 2023–2024 validation, 2025 test, 2026 complément | Examen du changement par rapport à R2 et des effectifs admissibles non encore calculés |
| Qualité et scores | Strict commun A/B ; fenêtres de 24 cibles complètes en principal | Couverture du panel et politique d'absence d'historique |
| Références | Persistance, jour UTC précédent, semaine UTC précédente | Âge maximal pour persistance ; variantes locales et disponibilité |
| Extensions | Sensibilité aux délais, combinaison fixe quotidienne/hebdomadaire | Compléments méthodologiques proposés, non intégrés automatiquement |
| Validation externe | Aucune revendication de test entièrement inédit sur les années explorées | Future confirmation sur observations non explorées, hors mission actuelle |
| Variables externes | Pas de météo ni de calendrier externe non vérifié | Archives de prévisions, périmètres, licences et dates de publication |

Ces choix relèvent du protocole de recherche proposé. Ils ne sont pas attribués artificiellement à un cours particulier de M1. Aucun choix restant incertain n'est converti en fait établi pour simplifier l'implémentation.

## 9. Vérifications documentaires de la mission

Seul le présent rapport est créé. Le README, les données, les préparations, le notebook et les figures restent inchangés. Aucun notebook de modélisation, variable prédictive, ajustement, prévision ou score n'est produit.

Contrôles prévus à l'issue de la rédaction, dont les résultats effectifs sont présentés dans le compte rendu d'exécution :

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe scripts/check_documentation.py --include-untracked
git diff --check
git status -sb
```

Comme le document est nouveau, un contrôle complémentaire de ses espaces en fin de ligne et de ses liens internes est nécessaire : `git diff --check` ne couvre pas les fichiers non suivis. La cohérence documentaire porte notamment sur les bornes UTC, les effectifs et masques de R4–R5, l'absence d'imputation et les incertitudes physiques et de publication. Aucune nouvelle consultation réseau n'est revendiquée.
