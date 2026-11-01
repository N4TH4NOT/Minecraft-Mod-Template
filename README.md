# Minecraft Mod Template — 1.21.10

Template pour les futurs projets Minecraft **1.21.10** : mods Fabric,
Forge et NeoForge sous Java 21, ou serveur Minestom sous Java 25.
`common/` partage le code des mods ; `minestom/` est une application
autonome, avec son propre build Gradle.

## Configuration

Les versions du jeu, des modloaders et des dépendances du mod sont définies
dans `gradle.properties`. Le wrapper racine fournit Gradle 8.14.6 pour les
mods ; celui de `minestom/` fournit Gradle 9.1.0 pour Java 25. Une installation
globale de Gradle n’est pas nécessaire. Utiliser le JDK complet de la cible.

Consulter [la configuration et les versions compatibles](docs/configuration.md),
[l’organisation](docs/organisation.md) et [les règles de versionnement](docs/versionnement.md).
Les consignes de contribution sont dans [AGENTS.md](AGENTS.md).

`common/` est obligatoire. Pour retirer une cible, supprimer simplement
son dossier `fabric/`, `forge/`, `neoforge/` ou `minestom/` : Gradle et la
CI l’excluent automatiquement. Les modules, versions, JDK et paramètres de
développement sont centralisés dans `gradle.properties` ; les scripts de
build des cibles sont dans `gradle/modules/`.

Pour réintroduire une cible, créer son dossier vide (ou avec `.gitkeep`).
La prochaine configuration Gradle génère ses sources, ressources et tests
d’exemple depuis `gradle/templates/`. Les fichiers existants sont conservés.
Minestom reçoit également son wrapper et son point d’entrée autonome.
L’initialisation seule est disponible avec :

```sh
./gradlew -p gradle/bootstrap help
```

Cette commande ne configure ni ne compile les applications. Consulter
[la configuration centralisée et l’initialisation](docs/developpement.md).

Avant les tâches, Gradle affiche les modules avec compilation planifiée,
les dossiers absents exclus et les modules présents non sélectionnés.
Ce bilan est aussi publié dans la synthèse de la CI.

## Validation

Les compilations et les tests s’exécutent exclusivement dans GitHub Actions,
via le workflow **Validate template or build project**. La CI adapte ses contrôles au
statut GitHub du dépôt :

- **Template** (`is_template=true`) : validation de la structure, des
  configurations et de l’outillage de CI, avec des tests d’initialisation
  sur des fixtures Gradle. L’absence de code applicatif est acceptée ;
  aucune compilation applicative n’est exigée.
- **Projet dérivé** : compilation et tests des seules cibles présentes,
  avec les versions de Java et de Gradle adaptées à chaque cible. Les
  rapports et les artefacts sont conservés. Une suite absente ou entièrement
  ignorée ne compte pas comme validation.

Le déclenchement manuel permet de choisir `repository_type=template` ou
`project` pour vérifier les deux parcours ; `auto` suit le statut GitHub.
Consulter [les contrôles et leur portée](docs/validation.md).

Avant l’approbation, la CI confirme aussi l’existence des versions épinglées
dans les métadonnées des dépôts officiels : plugins, bibliothèques, Gradle
et Minecraft. Ce contrôle ne télécharge aucun JAR ou ZIP et ne modifie pas
`gradle.properties` et conserve un rapport avec les sources consultées.
Une version introuvable ou une vérification réseau impossible empêche la validation.

En mode projet, les tests vérifient les métadonnées générées, les classes
d’entrée, les mixins, les services de plateforme et le format des ressources.
Ils ne remplacent pas un essai de démarrage du jeu.

Dans ce même mode, le test Minestom démarre et arrête un serveur local
sur un port éphémère.
Il ne nécessite aucune fonctionnalité métier du futur projet.

La publication Maven est facultative : définir `local_maven_url` uniquement
pour publier vers un dépôt choisi. Cette variable n’est pas requise pour
compiler ou tester.

## Cible Minestom

Minestom est un serveur autonome et possède sa propre API. Le module ne
charge pas les mods Fabric, Forge ou NeoForge et ne réutilise pas les classes
`net.minecraft` de `common/`. Son exemple de démarrage et son test servent
de base au futur serveur. Voir [la configuration Minestom](docs/minestom.md).

## Mise à jour des dépendances

Les tâches Gradle `checkModUpdates` (aperçu) et `updateModVersions` (application)
sont disponibles dans IntelliJ, fenêtre **Gradle → Tasks → mod development**.
Elles actualisent les versions compatibles dans `gradle.properties` en
conservant la version Minecraft du projet.

Pour rechercher et appliquer les versions avant chaque construction et ses
tests, activer `autoUpdateModVersions=true` dans l’environnement Gradle :
`-PautoUpdateModVersions=true`, variable d’environnement
`ORG_GRADLE_PROJECT_autoUpdateModVersions=true`, ou propriété dans
`gradle.properties`. Le mode automatique est désactivé par défaut et
nécessite le cache de configuration désactivé.

Le workflow manuel propose également le booléen **update_mod_versions**.
Consulter [les modes d’utilisation et les limites](docs/mises-a-jour.md).

## Credits
* [MultiLoader-Template](https://github.com/jaredlll08/MultiLoader-Template) by *jaredlll08*: for compatibility for main modloaders (Fabric, Forge and NeoForge)
