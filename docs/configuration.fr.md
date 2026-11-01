[English](configuration.md) | [Français](configuration.fr.md)

# Configuration de Minecraft 1.21.10

[`gradle.properties`](../gradle.properties) centralise l’identité du projet,
les modules, les versions et les paramètres de développement. Les scripts
des cibles se trouvent dans `gradle/modules/` ; leurs sources et sorties
restent dans les dossiers des modules.

## Java et Gradle

| Cible | JDK | Wrapper Gradle |
| --- | --- | --- |
| `common`, Fabric, Forge, NeoForge | 21 | 8.14.6 à la racine |
| Minestom autonome | 25 | 9.1.0 dans `minestom/` |

`<module>_java_version` règle le compilateur d’une cible, avec `java_version`
comme défaut. `gradle_java_version` et `minestom_gradle_java_version` règlent
la JVM qui exécute chaque build. Ce sont deux rôles distincts : changer
le compilateur ne change pas automatiquement la JVM de Gradle.

ForgeGradle 6 exige Gradle inférieur à 9. Java 25 nécessite Gradle 9.1 ou
plus récent, d’où le build Minestom séparé. Les distributions des wrappers
sont protégées par les propriétés `*_distribution_sha256`. Les tâches
de mise à jour des wrappers lisent les versions centrales ; voir
[le développement](developpement.fr.md).

## Versions retenues

Cette branche cible exactement Minecraft **1.21.10**. Les descripteurs des
mods excluent les versions suivantes du jeu.

| Dépendance | Version |
| --- | --- |
| Fabric Loader | 0.20.1 |
| Fabric API | 0.138.4+1.21.10 |
| Forge | 60.1.18 |
| NeoForge | 21.10.64 |
| NeoForm | 1.21.10-20251010.172816 |
| Parchment | 1.21.10 / 2025.10.12 |
| Cloth Config Fabric | 20.0.149 |
| Mod Menu | 16.0.1 |
| Mixin | 0.8.7 |
| MixinExtras | 0.5.5 |
| Minestom | 2025.12.19-1.21.10 |

| Plugin de build | Version |
| --- | --- |
| Fabric Loom | 1.13.6 |
| ModDevGradle | 2.0.148 |
| ForgeGradle | 6.0.54 |
| MixinGradle | 0.7.38 |
| Foojay resolver | 1.0.0 |

Parchment est résolu depuis le miroir Maven NeoForge. MixinExtras embarque
le runtime propre à chaque modloader avec la même version que celle de
compilation. Les formats des packs Minecraft sont **69** pour les ressources
et **88** pour les données ; `pack.mcmeta` déclare aussi `min_format` et
`max_format`.

Les tâches `checkModUpdates` et `updateModVersions` conservent la version
Minecraft. Elles laissent Java, Gradle, les plugins et Minestom inchangés :
voir [les mises à jour](mises-a-jour.fr.md). Pour Minestom, choisir une version
publiée pour le jeu ciblé, comme décrit dans [sa configuration](minestom.fr.md).

## Modules et validation

`modules`, `required_modules` et `standalone_modules` pilotent Gradle et la
CI. `common/` est obligatoire ; une cible absente est exclue. Un dossier
de cible vide, ou contenant seulement `.gitkeep`, est initialisé depuis
`gradle/templates/` sans modifier les dossiers déjà remplis.

Les quatre cibles passent un `PlatformContext` à `CommonClass.init`.
Minestom partage seulement les trois classes neutres `Constants`,
`CommonClass` et `PlatformContext` ; les API des moteurs restent dans leurs
cibles respectives.

En mode template, la CI accepte l’absence de code applicatif et vérifie
le modèle et ses outils. Le mode projet compile les cibles présentes et
exécute leurs tests. Les tests de métadonnées des mods ne démarrent pas
Minecraft ; le test Minestom démarre réellement un serveur. Les rapports
sont conservés, y compris en cas d’échec. Voir [la validation](validation.fr.md).

La publication Maven est facultative : définir `local_maven_url` uniquement
pour publier vers le dépôt choisi. Aucun secret de publication n’est requis
pour les constructions ou les tests.

Retour à [l’accueil](README.fr.md) et aux [consignes](AGENTS.fr.md).
