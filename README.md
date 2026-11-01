# Minecraft Mod Template — 1.21.10

Modèle Java 21 pour développer un mod Minecraft **1.21.10** avec Fabric,
Forge et NeoForge. Le code partagé se trouve dans `common/` ; chaque
modloader possède son module et ses tests automatisés.

## Configuration

Les versions du jeu, des modloaders et des dépendances du mod sont définies
dans `gradle.properties`. Le wrapper fournit Gradle 8.14.6 ; une installation
globale de Gradle n’est pas nécessaire. Utiliser un **JDK 21 complet**, avec
`javac`, pour le développement.

Consulter [la configuration et les versions compatibles](docs/configuration.md),
[l’organisation](docs/organisation.md) et [les règles de versionnement](docs/versionnement.md).
Les consignes de contribution sont dans [AGENTS.md](AGENTS.md).

## Validation

Les compilations et les tests s’exécutent exclusivement dans GitHub Actions,
via le workflow **Build Minecraft 1.21.10**, à chaque push ou pull request,
ou par déclenchement manuel. Sa matrice vérifie Fabric, Forge et NeoForge
séparément, ainsi que les tests partagés. Les rapports et les JAR sont
conservés comme artefacts du workflow.

Les tests de configuration vérifient les métadonnées générées, les classes
d’entrée, les mixins, les services de plateforme et le format des ressources.
Ils ne remplacent pas un essai de démarrage du jeu.

La publication Maven est facultative : définir `local_maven_url` uniquement
pour publier vers un dépôt choisi. Cette variable n’est pas requise pour
compiler ou tester.

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
