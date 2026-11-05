# Conventions temporelles et conception de l'agrégation horaire

Mission 007 — Phase 2. Projet M1 MIASHS 2026–2027.
Étude documentaire du 5 novembre 2026 ; aucune série horaire produite.

## 1. Sources consultées et niveau de preuve

### 1.1 Échelle de preuve

- **D — Direct** : déclaration attachée au jeu ODRÉ étudié, ou constat vérifiable dans son instantané. Un constat numérique ne prouve pas une convention physique.
- **C — Contexte officiel** : documentation RTE d'un autre produit, notamment éCO2mix ; elle n'est pas transposable automatiquement.
- **P — Proposition** : définition mathématique ou politique de préparation proposée pour notre projet, à valider.
- **N — Non confirmé** : information insuffisante dans les sources effectivement consultées. Cela ne prouve pas qu'aucune documentation n'existe ailleurs.

### 1.2 Références officielles et repères précis

| Réf. | Titre et URL | Section ou page consultée | Portée |
|---|---|---|---|
| S1 | [ODRÉ — Consommation quotidienne brute](https://odre.opendatasoft.com/explore/dataset/consommation-quotidienne-brute/) | Description du jeu ; onglet Informations / schéma, également visible dans les [résultats de la vue anglaise](https://odre.opendatasoft.com/explore/dataset/consommation-quotidienne-brute/?flg=en-us) | D, avec réserve sur les versions indexées et le rendu dynamique |
| S2 | [ODRÉ — Métadonnées API du jeu](https://odre.opendatasoft.com/api/explore/v2.1/catalog/datasets/consommation-quotidienne-brute) | Copie acquise : `data/raw/odre_f6gejuyq/metadata.json`, `fields`, `metas.default`, `metas.dcat`, `metas.custom` | D pour l'instantané téléchargé ; fichier local relu dans cette phase, pas de nouvel appel API |
| S3 | [RTE — Spécification des fichiers de données en puissance pour éCO2mix](https://assets.rte-france.com/prod/public/2025-06/Eco2mix%20-%20Sp%C3%A9cifications%20des%20fichiers%20en%20puissance.pdf) | PDF de juin 2025 : §1.1, p. 1 ; §3.1, tableau Date/Heures/Consommation p. 4 ; texte sur le pas demi-horaire p. 6 | C : fichiers éCO2mix, pas une spécification de la transformation ODRÉ |
| S4 | [RTE — Spécification des fichiers de données en puissance pour éCO2mix depuis la version 7.1](https://assets.rte-france.com/prod/public/2020-07/%C3%A9CO2mix%20-%20Description%20des%20fichiers%20des%20donn%C3%A9es%20en%20puissance.pdf) | PDF hébergé sous 2020-07 : §1.1 p. 1, tableau §3.1 p. 4 et pas demi-horaire p. 5 | C : documentation antérieure, pas une preuve couvrant chaque millésime ODRÉ |
| S5 | [RTE — Téléchargez l'historique des indicateurs éCO2mix](https://www.rte-france.com/donnees-publications/eco2mix-donnees-temps-reel/telecharger-indicateurs) | « Zoom sur les données téléchargeables », lien documentaire du 24 juin 2025 et paragraphes sur les corrections des historiques ; « Profondeur des historiques » | C : calendrier de révision d'éCO2mix |
| S6 | [RTE — Changement d'heure : quel impact sur l'activité de RTE ?](https://www.rte-france.com/getPDF?uuid=3bbf009a-ca0c-40f0-9b45-1c6958066f13) | Note du 25 octobre 2019, p. 1, paragraphe sur l'activité des prévisionnistes | C : nécessité d'une 25e heure, pas une explication des erreurs de l'export ODRÉ |

Les PDF S3, S4 et S6 et la page S5 ont été ouverts via l'outil de consultation web. Les recherches ciblées ODRÉ/RTE sur « horodatage », « début », « fin », « intervalle » et changement d'heure n'ont pas fourni de spécification directement applicable qui lève les incertitudes ci-dessous. Certaines pages secondaires renvoyées par le moteur ne sont pas utilisées comme preuves. Aucun export d'observations n'a été téléchargé.

### 1.3 Références locales

Ont également été examinés : `AGENTS.md`, l'état Git, le rapport de phase 1 et les éléments du diagnostic temporel des missions précédentes. L'instantané et le rapport de phase 1 fixent les données étudiées ; cette étude ne prétend pas décrire les mises à jour ultérieures du portail.

- Brut : `data/raw/odre_f6gejuyq/observations.json`.
- Grille : `data/processed/electricite_30min_phase1.jsonl`.
- Diagnostic : `reports/diagnostic_anomalies_temporelles.md`.
- Préparation : `reports/preparation_electricite_phase1.md`.

Les 258 574 étiquettes de grille, 258 521 puissances disponibles, 22 ambiguïtés et 31 absences sont les résultats de phase 1, pas de nouveaux résultats horaires. Aucune couverture horaire n'a été calculée pendant cette étude.

## 2. Conventions confirmées et non confirmées

### 2.1 Conclusions directement applicables à l'instantané ODRÉ

| Question | Conclusion | Preuve |
|---|---|---|
| Variable électrique et unité | `consommation_brute_electricite_rte`, consommation électrique en MW au pas de 30 minutes | D : S2, objet `fields` de ce nom, attributs `description` et `label` ; S1, description |
| Territoire | France métropolitaine hors Corse | D : même champ S2 et description S1 |
| Fuseau déclaré | UTC pour le jeu et horodatages exportés avec offset ; cela ne définit pas le support physique des mesures | D : S2, `metas.default.timezone = UTC` ; diagnostic local de `date_heure` |
| Fréquence de publication annoncée | Mensuelle, historique annoncé 2012 à date M−1 | D : S2, `metas.dcat.accrualperiodicity` et `metas.custom.profondeur-dhistorique` ; pas une garantie de publication immédiate |
| Description de l'étiquette | `date_heure`, `date` et `heure` n'ont pas de description sémantique renseignée | D : S2, objets `fields` correspondants |

MW est une unité de puissance. Une cadence de 30 minutes ne permet pas à elle seule de choisir entre un échantillon instantané et une moyenne sur un intervalle de cette durée. Une étiquette UTC lisible ne garantit pas non plus que la transformation de l'heure d'origine soit correcte partout.

### 2.2 Nature physique : ce que RTE établit, et ce qui reste à relier

S3, §1.1 p. 1, distingue pour éCO2mix : puissance instantanée en temps réel ; puissance moyenne pour les données consolidées et définitives. Le texte de la p. 6 fournit ces dernières au pas demi-horaire. **Ce fait est confirmé pour le produit documenté éCO2mix (C).**

S4, §1.1 p. 1, décrit également des sources de comptage pour consolidé/définitif et le texte p. 5 donne le pas demi-horaire ; sa formulation n'établit pas le rattachement temporel des moyennes ODRÉ. La concordance des producteurs, unités, fréquences et statuts rend une filiation plausible, mais aucune source consultée ne décrit l'ensemble des transformations jusqu'à notre champ ODRÉ.

Pour « chaque valeur de ce jeu ODRÉ est une moyenne sur exactement 30 minutes, sur toute sa période » : **Je ne peux pas confirmer cette convention à partir des sources consultées.** La nature moyenne est une hypothèse fortement étayée par le contexte RTE, pas une spécification directe du jeu. Le mois dont le statut est absent ne doit pas être assimilé automatiquement à l'une des catégories éCO2mix.

### 2.3 Début, fin ou autre référence de l'intervalle

Ni les descriptions de champs S2 ni les passages pertinents de S3/S4 ne fixent pour `date_heure` le début, la fin ou le centre d'une demi-heure. Le terme « point horaire » des tableaux éCO2mix n'est pas une déclaration de support temporel.

**Je ne peux pas confirmer cette convention à partir des sources consultées.**

La conversion `date_heure` vers `Europe/Paris`, la présence de `00:00`, la continuité ou l'allure de la courbe ne suffisent pas à trancher. Retenir une convention parce qu'elle réduit les erreurs prédictives serait un choix guidé par l'évaluation, pas une validation physique.

### 2.4 Constance sur 2012–2026

Deux documents éCO2mix de versions différentes ne constituent ni un historique exhaustif des schémas, ni un journal des transformations ODRÉ. Les statuts réellement rencontrés divergent en outre de la description générale du jeu pour certaines années, comme établi dans le diagnostic précédent.

Concernant la constance de la nature des mesures, de leur rattachement temporel et du traitement des fuseaux pendant toute la période : **Je ne peux pas confirmer cette convention à partir des sources consultées.**

Le constat d'offsets UTC dans l'instantané actuel décrit son encodage, pas la méthode de conversion appliquée en amont à chaque millésime. La lecture actuelle des métadonnées ne permet pas de reconstruire leurs anciennes versions.

### 2.5 Changements d'heure et anomalies observées

Le diagnostic précédent relève 30 groupes dupliqués lors des passages au printemps, 28 créneaux absents lors des retours à l'automne, ainsi que trois groupes et trois trous hors transition en décembre. C'est une correspondance empirique vérifiée en mission 006 bis, sans explication causale du producteur.

S6 p. 1 confirme que la prévision RTE au passage à l'heure d'hiver doit comporter une 25e heure. Le document ne décrit pas les collisions UTC de notre jeu ni une suppression légitime de créneaux. Une journée locale courte ou longue n'engendre pas, par nécessité, un trou ou un doublon dans le temps UTC écoulé.

Pour une règle officielle expliquant et corrigeant ces anomalies dans cet export : **Je ne peux pas confirmer cette convention à partir des sources consultées.** L'hypothèse d'un traitement de calendrier local reste ouverte ; aucune réaffectation des valeurs n'est justifiée par cette seule hypothèse.

## 3. Comparaison des méthodes d'agrégation

Les formules ci-dessous sont des constructions méthodologiques (P), non des opérations effectuées sur nos fichiers. Posons `H = [h, h+1 h)` une heure UTC physique, `p(t)` la puissance et `P_t` une observation portant l'étiquette `t`. Le choix de bornes semi-ouvertes sert à ne pas compter deux fois les frontières ; il ne constitue pas une affirmation sur les étiquettes sources.

### 3.1 Deux moyennes demi-horaires correctement alignées

Si les valeurs sont des puissances moyennes sur deux intervalles adjacents de durée 0,5 h couvrant exactement H, alors :

`P_H = (P_1 × 0,5 h + P_2 × 0,5 h) / 1 h = (P_1 + P_2) / 2`, en MW.

`E_H = P_1 × 0,5 h + P_2 × 0,5 h`, en MWh.

La moyenne arithmétique est donc un cas particulier de moyenne pondérée par les durées. Elle n'est exacte comme moyenne horaire que si la nature, les supports, l'absence de recouvrement et la couverture complète sont établis. Le fait d'avoir deux lignes ne suffit pas : deux variantes du même créneau restent une seule demi-heure.

Si les moyennes portent des labels de début : `P_H = (P_h + P_{h+30 min})/2`.

Si elles portent des labels de fin : `P_H = (P_{h+30 min} + P_{h+1 h})/2`.

**Exemple purement synthétique :** des valeurs étiquetées 10:00 et 10:30 couvrent 10:00–11:00 dans la première convention ; elles couvrent 09:30–10:30 dans la seconde. Un regroupement identique déplacerait donc le support de 30 minutes. Renommer la ligne horaire ne corrige pas un mauvais choix de demi-heures.

Notre grille est une grille d'étiquettes, pas encore une table d'intervalles confirmés. Un regroupement par heure civile de l'étiquette ou un `resample` avec paramètres par défaut n'est donc pas une justification suffisante.

### 3.2 Agrégation explicite par intervalles — méthode privilégiée sous conditions

Après validation documentaire, attribuer à chaque observation un support `I_i = [début_i, fin_i)`, en UTC, sans écraser l'étiquette originale. Vérifier que les supports utilisés couvrent H exactement une fois, sans trou ni chevauchement. Si les deux demi-heures sont contenues entièrement dans H, calculer la moyenne pondérée par durée ci-dessus.

Pour des supports à cheval sur les heures, la formule `somme(P_i × durée(I_i ∩ H)) / durée(H)` suppose une puissance constante sur les fragments de chaque support, ou une information équivalente qui justifie le partage. Une moyenne sur l'ensemble d'un intervalle ne détermine pas exactement l'énergie de ses sous-intervalles. Il ne faut donc pas qualifier ce prorata d'exact sans hypothèse supplémentaire.

Si les étiquettes correspondent au centre des intervalles, les supports de 30 minutes pourraient chevaucher les frontières des heures UTC entières. Deux possibilités à valider : choisir une grille horaire décalée composée de supports entiers, ou accepter et documenter une approximation de répartition. Ne pas inventer des centres ou appliquer un décalage automatique aujourd'hui.

**Recommandation :** privilégier l'union de deux demi-heures physiques complètes, puis étiqueter la cible horaire par son début UTC dans la future table. Cette convention de sortie, qui serait notre choix explicite, est distincte de la convention source encore inconnue.

### 3.3 Si les observations sont instantanées

La moyenne de deux échantillons n'est pas en général la moyenne intégrale de la puissance pendant une heure. Une interpolation constante ou linéaire pourrait définir une approximation, mais introduirait une hypothèse non présente dans les deux valeurs.

Avec trois points instantanés aux bornes 0, 30 et 60 minutes, une approximation trapézoïdale donnerait `P_H ≈ (P_h + 2P_{h+30 min} + P_{h+1 h})/4`. Elle suppose un comportement linéaire entre points, exige le point final et n'est pas justifiée pour des valeurs déjà moyennées. Elle n'est ni sélectionnée ni appliquée ici ; elle pourrait aussi introduire une fuite si le point final futur était utilisé dans une variable explicative à l'origine.

### 3.4 Autres cas et méthodes à écarter

Si une ressource officielle fournissait de véritables énergies demi-horaires `E_i` en MWh, leur somme donnerait l'énergie horaire, puis la division par 1 h donnerait la puissance moyenne. Ce n'est pas l'unité documentée de notre champ : aucune conversion implicite MW → MWh n'est autorisée sans durée et nature confirmées.

Écarter la somme directe des MW, la moyenne d'une seule valeur lorsque l'autre manque, le mélange électricité/gaz, la moyenne de variantes contradictoires, le choix du premier doublon et le remplissage par interpolation. Une moyenne de deux échantillons pourrait être définie comme cible statistique conventionnelle, mais ne devrait alors pas être présentée comme une puissance moyenne physique horaire confirmée. Cette reformulation changerait la cible et exigerait une validation scientifique distincte.

## 4. Politique de qualité horaire proposée

Cette politique P s'appliquerait **après** confirmation des supports. Elle ne modifie pas les règles de phase 1 : une puissance conservée dans la grille peut rester non admissible pour une cible horaire stricte.

### 4.1 Deux niveaux explicites

- `power_computable` : deux supports distincts et résolus, puissances finies, couverture de 60 minutes sans trou ni recouvrement, convention source validée pour le segment concerné.
- `target_eligible_strict` : critères précédents, plus statuts sources connus selon un dictionnaire documenté et absence de discordance de calendrier non résolue sur les sources utilisées.

Le strict est proposé pour l'évaluation principale ; un éventuel jeu secondaire pourra conserver des puissances calculables avec qualité dégradée. Aucune valeur manquante de la cible stricte ne serait remplacée par une valeur secondaire silencieusement. Ces deux niveaux et leur incidence doivent être validés et comptés avant modélisation.

| Situation demi-horaire | Politique proposée pour la future cible |
|---|---|
| Deux demi-heures distinctes, résolues et admissibles | Moyenne pondérée par durées ; couverture 60 min ; puissance horaire MW et provenance des deux supports |
| Une demi-heure absente, ou bord de fichier incomplet | Cible manquante ; raison `incomplete_coverage` ; pas de moyenne sur la seule valeur présente |
| Une demi-heure ambiguë | Cible manquante ; raison `ambiguous_component` ; conserver toutes les variantes, sans choix ni moyenne |
| Doublon de même puissance résolu en phase 1 | Compter un support, pas deux ; conserver tous les identifiants sources et le flag de doublon ; appliquer aussi les contrôles de statut et de calendrier |
| Statut RTE manquant dans une source | Ne pas fabriquer de statut. Si supports validés indépendamment, puissance secondaire calculable, mais cible stricte manquante pour qualité inconnue. Sans validation de la nature de ce segment, ne pas calculer de puissance physique horaire |
| Statuts distincts entre deux demi-heures ou variantes | Garder tous les statuts ; indicateur `mixed_status`. Pas de hiérarchie imposée à l'intérieur d'ODRÉ à partir d'une règle éCO2mix. L'admissibilité dépend du dictionnaire de statuts et des natures validées |
| Calendrier brut discordant avec la conversion UTC → Paris | Conserver le fait ; ne pas choisir une variante sur cette seule base. Cible stricte manquante tant que la discordance n'est pas résolue ; conserver l'éventuelle valeur secondaire et sa provenance |
| `flag_ignore` présent | Propager ses valeurs sources, sans interprétation ni filtre ; signaler toute nouvelle valeur |
| Passage été/hiver | Assembler en UTC. Préserver les occurrences locales distinctes, offsets et `fold`. Ne ni ajouter une heure locale inexistante ni fusionner l'heure répétée. Les trous réels restent des trous |

Les statuts manquants couvrent septembre 2026 selon le diagnostic précédent ; ce constat ne prouve pas que leurs puissances aient une autre nature physique. Les 11 doublons de même puissance présentent également des divergences entre variantes : leur valeur conservée en phase 1 n'implique pas une qualité stricte validée.

### 4.2 Métadonnées à propager et contrôles futurs

Proposer : début/fin UTC de cible, durée couverte, identifiants des demi-heures, positions sources et empreinte du brut, puissance candidate, cible stricte, tous les statuts et flags, raisons d'inadmissibilité multiples, indicateurs d'ambiguïté/absence/doublon/calendrier, version de politique et justification de la convention physique. Ne pas réduire plusieurs motifs à une seule étiquette qui masquerait les autres.

Avant une future génération : vérifier clé UTC unique, durées, exactement deux supports résolus par heure admissible, absence de double comptage, cohérence MW/MWh et provenance. Si la convention fin d'intervalle est confirmée, vérifier spécialement les premières/dernières heures et les frontières des blocs. Les 22 ambiguïtés et 31 absences ne permettent pas de déduire le nombre d'heures invalides par une simple division par deux ; ce compte dépend de l'alignement et de leur position.

## 5. Définition proposée de la cible à J+1

### 5.1 Définition physique conditionnelle

Une fois la convention confirmée, définir pour chaque heure UTC H : `Y_H = intégrale_H p(t) dt / 1 h`, en MW, pour la France métropolitaine hors Corse. En pratique, utiliser deux puissances moyennes demi-horaires couvrant H si les preuves requises sont obtenues. Ce choix ne signifie pas que l'étiquette source marque le début de H.

### 5.2 Option A — Les 24 prochaines heures, cohérente avec le protocole initial

Proposition conservant l'origine envisagée en mission 005 : émission `T = 00:00 UTC` chaque jour. Prévoir les 24 moyennes sur `[T+k h, T+(k+1) h)`, `k = 0,…,23`. L'horizon 1 désigne la première heure à venir ; son début est à T et sa fin à T+1 h. La dernière heure se termine à T+24 h.

Il s'agit de 24 heures écoulées. Le même T correspond à 01:00 ou 02:00 françaises selon la saison ; cette fenêtre n'est donc pas le lendemain civil français. La dénomination rigoureuse serait « prévision des 24 prochaines heures » plutôt que laisser « J+1 » sans définition.

**Recommandation principale pour rester cohérent avec la mission 005 : retenir A sous réserve de validation, sans l'assimiler au jour civil local.** L'émission n'autorise à utiliser que des variables publiées à T. Le fait qu'une heure soit théoriquement achevée avant T ne garantit pas que ses mesures sont déjà accessibles.

### 5.3 Option B — Véritable jour civil français J+1

Autre définition métier possible : émettre à 12:00 `Europe/Paris` le jour local D, pour le jour local D+1 compris entre ses deux minuits. Convertir séparément ces deux minuits en UTC, puis énumérer les heures physiques entre eux. Ne pas calculer la fin par « début + 24 h UTC ».

Cette cible comporte 23, 24 ou 25 moyennes horaires. L'émission à midi du jour précédent est un choix du projet, pas un horaire réglementaire ou RTE vérifié. Les délais des horizons dépendent de la saison et d'une éventuelle transition ; ils doivent être calculés à partir des instants UTC, pas supposés constants.

Une structure à 24 sorties fixes n'est pas directement adaptée : il faudrait soit une sortie par intervalle avec identifiants UTC et longueur variable, soit une représentation avec masque explicitement conçu, sans inventer de valeur pour une heure absente. En automne, les deux heures locales répétées sont deux cibles distinctes. S6 p. 1 confirme l'enjeu de la 25e heure pour les prévisionnistes RTE.

### 5.4 Option C — Jour UTC suivant, 24 sorties fixes

Une variante « jour à venir » à taille fixe consisterait à émettre à 12:00 UTC du jour D pour `[00:00 UTC de D+1, 00:00 UTC de D+2)`. Il y aurait 24 sorties : première heure débutant à T+12 h et dernière finissant à T+36 h. Ce ne seraient pas les 24 prochaines heures et cela ne couvrirait pas le lendemain civil local.

Les options A, B et C sont des protocoles différents ; leurs performances ne seraient pas directement comparables sans aligner origines, cibles et informations. Aucune option n'est implémentée pendant cette phase. Le choix B ou C modifierait la proposition d'origine de mission 005 et doit être annoncé comme tel.

## 6. Risques méthodologiques

1. **Décalage de cible** : une convention début/fin erronée décale de 30 minutes les supports, modifie les paires et peut transformer un retard en utilisation du futur.
2. **Mesure et publication** : S5, section sur les corrections, décrit des révisions éCO2mix mensuelles puis annuelles ; S2 annonce une publication ODRÉ mensuelle. Cela ne justifie pas une disponibilité opérationnelle immédiate des puissances d'archive. Les délais exacts et versions disponibles à T restent à établir pour notre jeu.
3. **Archive révisée** : utiliser une version finale comme prédicteur historique simule une information potentiellement indisponible à l'époque. Nommer cette hypothèse dans tout backtest rétrospectif ; ne pas annoncer une validation opérationnelle sans archives de publication ou autre source adaptée.
4. **Fenêtres et prétraitements** : calculer les historiques exclusivement avant l'origine en respectant supports et disponibilité ; aucune fenêtre centrée, interpolation future, statistique ajustée sur validation/test ou vraie consommation des premiers horizons injectée dans les suivants.
5. **Statuts et masques** : un statut final, un flag ou une révision futurs ne sont pas nécessairement connus à T. Les indicateurs de qualité servent d'abord à l'audit des cibles ; leur usage comme prédicteurs doit respecter leur disponibilité. Un masque d'évaluation rétrospectif n'est pas une information de production connue à l'avance.
6. **Transitions et références naïves** : un retard de 24 h UTC est une durée écoulée, pas toujours la même heure locale de la veille. Les références à calendrier local demandent une règle séparée sur les jours de transition.
7. **Biais d'exclusion** : quarantaines et trous sont saisonniers. Compter les cibles exclues par année, saison, transition et horizon et comparer toutes les méthodes sur un masque commun défini avant les scores. Ne pas supprimer les journées difficiles après examen des erreurs.
8. **Conservation des preuves** : aucune correction des anomalies par choix arbitraire d'une occurrence, déplacement de date ou interpolation. Une convention validée pour un segment ne suffit pas à certifier toute la période.

La documentation disponible justifie d'étudier une moyenne pondérée, mais pas de lancer une agrégation physique définitive dès maintenant. L'absence d'information n'est pas résolue en choisissant les paramètres logiciels les plus commodes.

## 7. Décisions à valider avant implémentation

| Décision | Proposition et condition |
|---|---|
| Nature du champ ODRÉ | Obtenir une preuve directement applicable de puissance moyenne demi-horaire, ou valider explicitement une hypothèse limitée et un protocole de sensibilité ; aucune certification physique sans preuve |
| Support de l'étiquette | Confirmer début, fin, centre ou autre référence, avec éventuelles variations par période ; bloquant pour choisir les paires |
| Filiation et historique | Clarifier la transformation depuis RTE/éCO2mix et son traitement des changements d'heure ; demander aussi les anomalies de décembre et les statuts divergents |
| Définition de J+1 | Valider A (proposition principale : 24 prochaines heures, origine 00:00 UTC), B (jour français variable), ou C (jour UTC suivant) |
| Admissibilité horaire | Valider la séparation puissance calculable / cible stricte, les statuts connus et la quarantaine des discordances ; ne pas réinterpréter le nombre « exploitable » de phase 1 comme une garantie stricte |
| Conflits et absences | Maintenir valeurs manquantes explicites et provenance, sans moyenne des variantes ni imputation |
| Disponibilité des prédicteurs | Établir date de publication/révision, délai admissible et hypothèse opérationnelle ou rétrospective ; report de la météo sans source de prévisions datées |
| Implémentation ultérieure | Documenter supports, bornes, labels de sortie, masque et tests synthétiques début/fin/centre, frontières, 23/25 heures, statuts et anomalies ; aucune génération avant accord |

Les questions au producteur sont proposées, mais aucun contact n'a été effectué. Une décision explicite de travailler sous hypothèse doit demeurer présentée comme hypothèse et ne transforme pas la convention en fait établi.

## 8. Vérifications de cette phase

- Lecture préalable de `AGENTS.md` et de l'état Git ; modifications et fichiers non suivis préexistants conservés.
- Empreintes relevées avant et après l'étude, sans modification attendue :
  - brut : `65f6a751d0e02d1a11c6d5e85dc620734b04ffc19f2c2ed3acc110e828125cf3` ;
  - grille demi-horaire : `50a3e89a7f9bbd5325ad1e4f557e6a3081ad7d5a429d6f9143f255b8f1172762` ;
  - script de phase 1 : `32c4e195418d9375d6750cb306d024812d8b555d50ad146af7ab15a9b9ddce19` ;
  - tests de phase 1 : `8ad000db32d17e0ecd697a01121c9d7428a605a341a4294a6540591b254616a3`.
- Aucun nouveau test de code ou résultat statistique annoncé : la phase est documentaire. Les résultats des tests de phase 1 restent ceux de son rapport, pas une nouvelle exécution.
- Seul `reports/etude_agregation_horaire.md` est créé. Aucun fichier existant modifié, aucun téléchargement d'observations, série horaire, modèle, commit ou push. Attente de validation avant implémentation.
