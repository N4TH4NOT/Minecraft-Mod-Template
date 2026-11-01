[English](developpement.en.md) | [Français](developpement.md)

# Développer à partir du template

Modifier `gradle.properties` pour configurer Gradle et la CI. Voir
[l’organisation](organisation.md) pour trouver le code et les ressources.

## Paramètres centraux

| Propriétés | Rôle |
| --- | --- |
| `modules`, `required_modules`, `standalone_modules` | Modules déclarés, obligatoires et autonomes |
| `project_name`, `version`, `group`, `mod_*`, `minestom_main_class` | Identité du projet et des sources initiales |
| `java_version`, `<module>_java_version`, `buildsrc_java_version` | JDK de compilation des modules et de l’outillage |
| `gradle_java_version`, `minestom_gradle_java_version` | JDK qui lance chaque build Gradle |
| `gradle_version`, `minestom_gradle_version`, `*_distribution_sha256` | Versions et empreintes des wrappers |
| Versions des plugins et bibliothèques | Dépendances des scripts centraux |
| `run_*_directory`, `generated_resources_directory`, `java_encoding`, `test_max_heap_size` | Chemins, encodage et mémoire des tests |
| `minestom_development` | Mode de développement du contexte Minestom, désactivé par défaut |

Choisir l’identité avant de générer les sources : modifier ensuite `group`
ou `mod_id` ne renomme pas le code existant. Consulter les
[versions de référence](configuration.md) et les [règles de versionnement](versionnement.md).

## Ajouter ou retirer une cible

`common/` est obligatoire. Supprimer un dossier `fabric/`, `forge/`,
`neoforge/` ou `minestom/` l’exclut de Gradle et de la CI, sans modifier la
liste centrale ni recréer le dossier absent.

Pour réintroduire une cible déclarée, créer son dossier vide, ou avec
`.gitkeep` seul, puis lancer depuis la racine :

```sh
mkdir forge
./gradlew -p gradle/bootstrap help
```

Le bootstrap copie les exemples de `gradle/templates/` avec l’identité
configurée, sans construire les applications ni modifier les dossiers non
vides. Une configuration Gradle habituelle initialise aussi les cibles.
Pour Minestom vide, utiliser d’abord ce bootstrap pour créer son wrapper.

## Contexte du code partagé

Les quatre cibles appellent `CommonClass.init(context)` avec un
`PlatformContext` : nom, mode de développement et prédicat de recherche des mods.
Fabric, Forge et NeoForge utilisent `common/`, qui garde l’accès à Minecraft vanilla.
Minestom compile uniquement `Constants`, `CommonClass` et `PlatformContext`
depuis le package `group`. Ces trois classes restent neutres ; le build
`common/`, NeoForm et les ressources de mixins ne sont pas inclus dans Minestom.

Exemple dans le point d’entrée Fabric, avec `net.fabricmc.loader.api.FabricLoader` importé :

```java
var loader = FabricLoader.getInstance();
var context = new PlatformContext("Fabric", loader.isDevelopmentEnvironment(),
        loader::isModLoaded);
CommonClass.init(context);
```

Le code partagé utilise `context.isModLoaded().test(modId)`. Les appels aux
API des modloaders restent dans leurs modules ; le prédicat Minestom retourne
`false`. Pour partager d’autres classes neutres, adapter la sélection dans
`gradle/modules/minestom.gradle`.

## JDK et wrappers

Le JDK qui lance Gradle peut différer de celui qui compile les sources.
Par défaut : Java 21 et wrapper racine Gradle 8 pour les mods ; Java 25 et
wrapper Gradle 9 pour Minestom. La CI installe les JDK déclarés. Dans l’IDE,
importer le build racine pour les mods et le build `minestom/` séparément.

Conserver les scripts et JAR des wrappers. Après modification des versions
ou empreintes centrales, synchroniser les fichiers :

```sh
./gradlew wrapper
./minestom/gradlew -p minestom syncWrapperPreset
```

La seconde tâche synchronise aussi le preset Minestom. La CI refuse les
écarts avec les propriétés. Les références GitHub Actions restent épinglées dans le workflow.
Pour activer le mode de développement, utiliser `-Pminestom_development=true`
avec `run`, ou `JAVA_OPTS='-Dtemplate.development=true'` pour une distribution ;
voir [les exemples Minestom](minestom.md).

## Vérification

Les compilations et tests automatisés s’exécutent dans GitHub Actions ;
[le guide de validation](validation.md) en précise la portée. La CI indique
les modules sélectionnés et confirme les versions par leurs métadonnées.
Le [guide des mises à jour](mises-a-jour.md) décrit les tâches de recherche
et d’application des nouvelles versions. Voir aussi les
[consignes de contribution](AGENTS.fr.md) et le [README](README.fr.md).
