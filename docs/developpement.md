# Configuration centrale et initialisation des cibles

`gradle.properties` est la source des paramètres de Gradle et de la CI.
Les versions Java sont explicites ; aucun choix de JDK par analyse des
métadonnées ou du bytecode n’est effectué.

## Paramètres

| Propriétés | Rôle |
| --- | --- |
| `modules`, `required_modules`, `standalone_modules` | Cibles disponibles, obligatoires et autonomes |
| `java_version`, `<module>_java_version` | Toolchain par défaut et exceptions par module |
| `gradle_java_version`, `minestom_gradle_java_version` | JVM qui exécute chaque build Gradle |
| `buildsrc_java_version` | Toolchain de l’outillage, compatible avec la JVM Gradle |
| `gradle_version`, `minestom_gradle_version` et leurs `*_distribution_sha256` | Distributions des wrappers et empreintes |
| `*_version` des plugins et bibliothèques | Versions des dépendances de construction et de test |
| `run_*_directory`, `generated_resources_directory` | Chemins de développement relatifs aux modules |
| `test_max_heap_size`, `java_encoding` | Mémoire des tests et encodage des sources |
| `minestom_development` | Mode de développement transmis au contexte par la tâche Minestom `run` |
| `project_name`, `group`, `mod_id`, `mod_name`, `minestom_main_class` | Identité et fichiers initiaux du projet |

Par exemple, `forge_java_version` peut différer du défaut `java_version`.
Cela ne change pas automatiquement la JVM qui exécute Gradle. La CI installe
les JDK déclarés et vérifie leurs compatibilités avant une construction.
Les contraintes des plugins, notamment ForgeGradle, restent applicables.

Les références GitHub Actions restent épinglées dans le workflow : GitHub
ne permet pas de calculer dynamiquement ces références depuis les propriétés.
Les valeurs des fixtures de tests décrivent des cas de test et ne sont pas
des paramètres de production.

## Scripts de build

Les fichiers principaux des cinq cibles se trouvent dans `gradle/modules/`.
`settings.gradle` les associe aux dossiers correspondants ; `file('src/...')`
et les sorties `build/` restent relatifs à ces dossiers. Un `forge/build.gradle`
n’est donc plus nécessaire. Les conventions communes restent dans `buildSrc/`.
Un module personnalisé peut fournir son propre `build.gradle` lorsqu’il
n’existe pas de configuration centrale correspondante.

Minestom reste un build autonome : son petit `settings.gradle` sélectionne
`gradle/modules/minestom.gradle` et son wrapper fournit sa distribution Gradle.

## Contexte du code partagé

Les modules Fabric, Forge et NeoForge importent directement les classes de
`common/`, qui conserve l’accès aux API Minecraft vanilla. Minestom compile
seulement `Constants`, `CommonClass` et `PlatformContext` depuis ces mêmes
sources, sans charger le build `common/`. Ces trois classes restent neutres.
Les quatre points d’entrée appellent `CommonClass.init` avec un
`PlatformContext`. Ce record contient le nom de plateforme, l’indicateur de développement et un
`Predicate<String>` chargé de consulter les mods présents.

Par exemple, dans le point d’entrée Fabric, avec `FabricLoader` importé
depuis `net.fabricmc.loader.api` :

```java
var loader = FabricLoader.getInstance();
var context = new PlatformContext("Fabric", loader.isDevelopmentEnvironment(),
        loader::isModLoaded);
CommonClass.init(context);
```

Dans le code commun, la consultation passe par
`context.isModLoaded().test(modId)`. Forge et NeoForge fournissent leur propre
callback au même point d’entrée partagé, une fois leur API disponible.
Les appels aux API du modloader restent dans le module de la cible.
Minestom fournit aussi ce contexte depuis son initialisation autonome,
avec un prédicat qui retourne `false` pour la recherche de mods.
Son mode de développement est explicite ; voir
[les options de démarrage Minestom](minestom.md#exemple-fourni).

Le test de contrat du contexte emploie un prédicat de test, vérifie
l’identifiant demandé et les valeurs requises par le record. La CI compile
également cet exemple généré dans une fixture isolée ; les constructions
complètes des cibles restent couvertes par le parcours projet.

## Dossiers absents ou vides

Un dossier absent reste exclu. `common/` est obligatoire et ne peut pas
être supprimé. Pour initialiser une cible, créer son dossier vide, ou avec
un fichier `.gitkeep` seul, puis lancer une configuration Gradle.

```sh
mkdir forge
./gradlew -p gradle/bootstrap help
```

Le bootstrap affiche les fichiers à créer puis remplit le dossier depuis
`gradle/templates/`. Il ne configure pas les applications. Une commande
Gradle habituelle effectue aussi cette initialisation avant la sélection
des modules. Pour Minestom vide, utiliser d’abord le wrapper racine avec
le bootstrap afin de créer son propre wrapper.

Les presets fournissent les sources, ressources et tests d’exemple, avec
le package et l’identité configurés. Ils ne remplacent jamais un dossier
non vide. Les valeurs d’identité doivent donc être choisies avant
l’initialisation ; les changements ultérieurs du code existant restent
du ressort du développeur.

## Mise à jour des wrappers

Les wrappers doivent conserver leurs fichiers de démarrage physiques,
car ils interviennent avant la lecture de `gradle.properties`. Après une
modification des versions ou des empreintes centrales, les tâches Gradle
suivantes synchronisent leur configuration :

```sh
./gradlew wrapper
./minestom/gradlew -p minestom syncWrapperPreset
```

La seconde tâche met aussi à jour les launchers et le JAR du preset Minestom.
Son fichier de propriétés reste paramétré par les valeurs centrales.
La CI refuse une divergence entre wrappers et configuration centrale.

Avant l’approbation du template, la CI confirme également la publication
des versions épinglées des dépendances actives, par leurs métadonnées seules.
Aucun binaire n’est téléchargé. Le rapport **published-versions** expose
les sources et les résultats.
Ajouter une nouvelle dépendance de version nécessite aussi d’ajouter sa
règle de recherche dans `scripts/ci/validate_published_versions.py`.

Les compilations et tests automatisés restent exécutés exclusivement
dans GitHub Actions. Le bilan préalable distingue modules avec compilation
planifiée, cibles absentes et modules présents non sélectionnés.
