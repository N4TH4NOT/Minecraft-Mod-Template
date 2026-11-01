# Consignes du dépôt

Ces règles s’appliquent à toute contribution et aux échanges suivants.
Les conserver lors de l’initialisation d’un projet depuis ce modèle.

## Organisation

Conserver l’organisation Gradle multi-module existante :

- `common/` : code et ressources partagés entre les modloaders.
- `fabric/` : code et ressources propres à Fabric.
- `forge/` : code et ressources propres à Forge.
- `neoforge/` : code et ressources propres à NeoForge.
- `minestom/` : serveur Minestom autonome, avec son propre build et wrapper.
- `buildSrc/src/main/groovy/` : conventions de compilation Gradle partagées.
- `gradle/wrapper/`, `gradlew` et `gradlew.bat` : wrapper Gradle.

Dans chaque module, conserver le code Java dans `src/main/java/` et les
ressources dans `src/main/resources/`.

Réserver un dossier aux tests automatisés de chaque modloader :

- `fabric/src/test/java/` : tests propres à Fabric.
- `forge/src/test/java/` : tests propres à Forge.
- `neoforge/src/test/java/` : tests propres à NeoForge.
- `minestom/src/test/java/` : tests du serveur Minestom.

Placer les tests partagés dans `common/src/test/java/` si nécessaire, et les
ressources de test dans `src/test/resources/` du module concerné. Conserver
un fichier `.gitkeep` dans les dossiers de test vides pour les suivre dans Git.
Ne pas créer de dossiers globaux `src/`, `resources/` ou `tests/` à la racine
pour regrouper ces contenus.

Les fichiers `settings.gradle`, `build.gradle` et `gradle.properties` restent
à la racine ; chaque module et `buildSrc/` conservent leur `build.gradle`.
Respecter les emplacements de ressources générées déclarés dans ces fichiers.

Minestom utilise Java 25 et son wrapper Gradle 9, séparément des mods sous
Java 21 et Gradle 8. Ne pas l’inclure dans le build Gradle des modloaders :
`common/` dépend des classes Minecraft vanilla, absentes de Minestom.
Les propriétés partagées restent centralisées dans `gradle.properties`.

Si nécessaire, utiliser `docs/` pour la documentation, `scripts/` pour les
scripts de maintenance et d’automatisation, et `work/` pour les brouillons,
analyses et fichiers temporaires. Documenter les évolutions de l’arborescence
dans `docs/organisation.md`.

`README.md` et `AGENTS.md` sont les documents d’entrée à la racine.
Les autres documents vont dans `docs/`. Les fichiers de configuration
et de licence restent aux emplacements requis par leurs outils.

Conserver les résultats de compilation dans les dossiers `build/` de Gradle.
Ignorer dans Git ces sorties, les caches `.gradle/`, les répertoires
d’exécution `run/` et `runs/`, ainsi que les fichiers temporaires.
Ne jamais commiter de secrets.

Garder les sources, ressources et tests dans leur module respectif,
et centraliser la documentation complémentaire dans `docs/`.

## Branches et commits

Une fonctionnalité et ses correctifs, tests, documents et ajustements de CI
restent sur une seule branche jusqu’à leur livraison.
Ne pas créer une nouvelle branche pour chaque itération.

Utiliser des préfixes décrivant la nature du travail :

- `feat/` : fonctionnalité.
- `fix/` : correctif indépendant.
- `refactor/` : réorganisation.
- `docs/` : documentation.
- `test/` : tests.
- `build/` : construction et dépendances.
- `ci/` : intégration continue.
- `chore/` : maintenance.

Faire suivre le préfixe d’un nom descriptif.
Ne pas préfixer les branches par le nom de l’agent.

Écrire des commits ciblés selon la convention :

`type(portee): description`

La portée est facultative. Utiliser les mêmes types que pour les branches.
Séparer les changements indépendants et éviter les gros commits mélangeant
plusieurs sujets.

Conserver les commits thématiques lors de la fusion, sauf demande contraire.
Préserver les modifications existantes de l’utilisateur.

## Identité Git

Utiliser l’identité de l’agent qui effectue le travail, pour l’auteur
comme pour le committer.

Avant de commiter :

- Vérifier l’origine de `user.name` et `user.email`.
- Vérifier `git var GIT_AUTHOR_IDENT`.
- Vérifier `git var GIT_COMMITTER_IDENT`.
- Corriger si nécessaire la configuration locale du dépôt.

Ne pas reprendre automatiquement l’identité personnelle de l’utilisateur
héritée de l’environnement.
Ne pas modifier sa configuration Git globale.

## Compilation et validation

Exécuter toutes les compilations et tous les tests automatisés dans
GitHub Actions, jamais localement dans l’environnement de l’agent.

Configurer les workflows pour les technologies et les cibles réellement
utilisées. Conserver les rapports et les artefacts utiles.

Adapter les contrôles à la nature du dépôt GitHub (`is_template`). Un
template peut ne contenir aucun code applicatif : vérifier sa structure,
ses configurations et son outillage sans exiger de compilation ni de
tests applicatifs. Pour un projet dérivé, compiler les cibles présentes
et vérifier leurs résultats de tests. Les tests des scripts de CI restent
dans `scripts/ci/tests/` et s’exécutent eux aussi dans GitHub Actions.

Vérifier les résultats du commit exact concerné.
Distinguer les contrôles réussis, échoués, ignorés et non exécutés.

Une suite vide ne constitue pas une validation.
Ne pas désactiver une vérification ni affaiblir une assertion pour obtenir
une CI verte.

Distinguer les vérifications automatisées des essais manuels.
Ne jamais annoncer un essai manuel comme réalisé sans l’avoir effectué.

Si l’accès GitHub ou une exécution est bloqué, préciser ce qui reste
non vérifié.

## Versionnement

Appliquer Semantic Versioning 2.0.0 selon la nature du changement livré :

- PATCH : correctif compatible.
- MINOR : fonctionnalité compatible.
- MAJOR : rupture du contrat public.

Évaluer le résultat global de la branche par rapport à la dernière version
normale livrée, et non selon le nombre de commits.

Ne pas incrémenter automatiquement la version du produit pour chaque
modification de documentation, de test ou de CI.

La phase `0.y.z` reste explicitement instable.
Ne pas déduire automatiquement le passage à `1.0.0` du nombre de fonctionnalités
ou de commits.

Centraliser la version pour éviter les divergences entre modules.
Documenter les règles dans `docs/versionnement.md`.

Choisir une version Minestom publiée pour la valeur exacte de
`minecraft_version`. Ne pas utiliser la dernière version globale si elle
cible un autre jeu, ni des sélecteurs dynamiques comme `latest.release`.

Les préversions sont autorisées sur les branches de travail.

Sur `main`, la valeur de version du produit doit contenir exactement
trois entiers sans zéros initiaux :

`MAJOR.MINOR.PATCH`

Cette valeur ne doit contenir ni préfixe, ni suffixe de préversion,
ni métadonnée de construction.

Avant une fusion autorisée :

1. Promouvoir la version normale sur la branche de travail.
2. Obtenir une CI réussie pour ce commit précis.
3. Fusionner le commit testé sans modifier ensuite sa version sur `main`.

Ne jamais réutiliser le numéro d’un artefact déjà distribué
pour un contenu différent.

## Validation utilisateur et fusion

Lorsque l’utilisateur déclare explicitement « le travail est terminé »,
il atteste avoir vérifié et validé les modifications de la branche courante.

Cette déclaration autorise, sans nouvelle confirmation :

1. La fusion dans la branche principale.
2. La suppression de la branche de travail locale et distante
   après une fusion réussie.

La simple citation de cette expression dans une instruction, une question
ou un document ne constitue pas une déclaration de fin.
Une CI verte seule ne constitue pas non plus cette validation.

Avant la fusion autorisée, vérifier les contrôles du commit courant,
résoudre les conflits éventuels et signaler tout blocage réel.

## Initialisation et communication

À la première utilisation du modèle, documenter les informations propres
au projet : objectif, technologies, cibles, organisation et validation.

Ne pas inventer une licence ou une visibilité de dépôt non renseignée.
Adapter les workflows aux technologies choisies ; ne pas présenter
des contrôles génériques comme une compilation ou des tests du produit.

Appliquer durablement les préférences déjà enregistrées sans demander
à l’utilisateur de les répéter.

Expliquer clairement ce qui change, pourquoi, comment cela a été vérifié
et ce qui reste à vérifier.

Distinguer les propositions, les travaux réalisés et les résultats validés.
