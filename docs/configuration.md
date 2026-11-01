# Configuration Minecraft 1.21.10

Cette branche cible uniquement Minecraft 1.21.10, avec Java 21 pour les
modloaders et Java 25 pour le serveur Minestom autonome.
Les descripteurs Fabric, Forge et NeoForge excluent les versions suivantes
du jeu, dont la compatibilité n’est pas établie.

## Dépendances du mod

| Composant | Version retenue |
| --- | --- |
| Minecraft | 1.21.10 |
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
| Minestom (serveur autonome) | 2025.12.19-1.21.10 |

Versions contrôlées dans les métadonnées Maven officielles :
[Fabric Loader](https://maven.fabricmc.net/net/fabricmc/fabric-loader/maven-metadata.xml),
[Fabric API](https://maven.fabricmc.net/net/fabricmc/fabric-api/fabric-api/maven-metadata.xml),
[Forge](https://maven.minecraftforge.net/net/minecraftforge/forge/maven-metadata.xml),
[NeoForge](https://maven.neoforged.net/releases/net/neoforged/neoforge/maven-metadata.xml),
[Cloth Config](https://maven.shedaniel.me/me/shedaniel/cloth/cloth-config-fabric/maven-metadata.xml)
et [Mod Menu](https://maven.terraformersmc.com/releases/com/terraformersmc/modmenu/maven-metadata.xml).
Le [MDK NeoForge 1.21.10](https://github.com/NeoForgeMDKs/MDK-1.21.10-ModDevGradle)
confirme les versions NeoForm et Parchment.

Les mappings Parchment sont résolus directement depuis le miroir Maven
NeoForge. Cela évite la redirection du dépôt Parchment vers JFrog,
refusée par la politique réseau de cet environnement.

Cloth Config 21.11 cible Minecraft 1.21.11 ; cette branche conserve donc
la dernière version de la série 20. MixinExtras est embarqué avec le
runtime propre à chaque modloader pour aligner l’API de compilation et
la version réellement disponible en jeu.

Les formats Minecraft 1.21.10 sont 69 pour les ressources et 88 pour les
données. Le fichier `pack.mcmeta` décrit les ressources et déclare
`min_format` et `max_format`, requis pour ce format.

## Outillage

| Outil | Version retenue |
| --- | --- |
| Gradle | 8.14.6 |
| Gradle du build Minestom | 9.1.0 |
| Fabric Loom | 1.13.6 |
| ModDevGradle | 2.0.148 |
| ForgeGradle | 6.0.54 |
| MixinGradle | 0.7.38 |
| Foojay resolver | 1.0.0 |

ForgeGradle 6 exige Gradle inférieur à 9. Loom 1.13.6 est la dernière
version stable compatible avec Gradle 8 ; les versions suivantes exigent
Gradle 9. Le wrapper et sa distribution sont vérifiés par SHA-256.
Le remappage moderne de Loom n’utilise pas de refmap Mixin hérité.

Minestom pour Minecraft 1.21.10 exige Java 25. Son wrapper Gradle 9.1.0
et son build sont autonomes afin de conserver Gradle 8 pour Forge.
Voir [la cible Minestom](minestom.md).

## Validation et publication

Le workflow `.github/workflows/build.yml` valide la structure lorsqu’il
s’agit d’un template GitHub, même sans code applicatif. Dans un projet
dérivé, il sélectionne les cibles présentes. Les mods utilisent Temurin 21
et chaque tâche lance, dans GitHub Actions :

```sh
./gradlew --no-daemon --max-workers=2 --stacktrace :common:check :<modloader>:build
```

Les tests JUnit contrôlent les liens entre métadonnées et classes, la
découverte des services et les ressources traitées par Gradle. Les rapports
XML et HTML sont conservés même en cas d’échec. Le démarrage d’un client
ou serveur Minecraft n’est pas couvert par ces tests.

La variable `local_maven_url` n’est lue que pour déclarer un dépôt de
publication facultatif. Les tâches de compilation et de test n’exigent
aucun secret de publication. Ne jamais enregistrer de credentials dans
les fichiers de configuration.
