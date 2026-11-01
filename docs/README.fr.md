# Minecraft Mod Template — 1.21.10

[English](../README.md) · [Français](README.fr.md)

Template multi-cible pour Minecraft **1.21.10**. Configurer versions, modules et
JDK dans `gradle.properties` ; les scripts des cibles sont dans `gradle/modules/`.

| Cible | JDK | Wrapper |
| --- | --- | --- |
| Fabric, Forge, NeoForge | 21 | Racine : Gradle 8.14.6 |
| Serveur Minestom autonome | 25 | `minestom/` : Gradle 9.1.0 |

## Initialiser un projet

1. Créer un dépôt avec **Use this template**.
2. Définir l’identité du projet et les versions dans `gradle.properties`.
3. Conserver `common/` et au moins une cible. Supprimer les dossiers des cibles
   optionnelles pour les exclure de Gradle et de la CI.
4. Pour réintroduire une cible, créer son dossier vide puis l’initialiser :

```sh
mkdir forge
./gradlew -p gradle/bootstrap help
```

Les fichiers existants sont conservés. Les dossiers vides, même avec un seul
`.gitkeep`, reçoivent sources, ressources et tests d’exemple. Minestom reçoit
également son wrapper. Le bootstrap ne compile pas les applications.

## Partager du code

Fabric, Forge et NeoForge importent directement `common/`. Les quatre cibles
appellent `CommonClass.init(PlatformContext)` avec le nom de plateforme, le mode
de développement et un callback de recherche des mods. Minestom compile les
mêmes trois classes indépendantes du moteur : `Constants`, `CommonClass` et
`PlatformContext`.

Voir [le développement et le code partagé](developpement.md) et
[les options de démarrage Minestom](minestom.md).

## Valider les changements

Les compilations et tests automatisés s’exécutent dans **GitHub Actions**.

| Mode du dépôt | Contrôles |
| --- | --- |
| Template (`is_template=true`) | Structure, configuration, versions publiées et fixtures Gradle isolées ; le code applicatif peut être absent |
| Projet dérivé | Compilations, tests exécutés et artefacts des cibles présentes |

Le workflow **Validate template or build project** accepte `repository_type`
avec les valeurs `auto`, `template` et `project`. Il annonce les modules à
compiler, absents et non sélectionnés avant les builds. Le contrôle des
versions consulte les métadonnées officielles sans télécharger les binaires.

Voir [les contrôles et limites de la CI](validation.md). Les tâches
`checkModUpdates` et `updateModVersions` conservent la version Minecraft ;
[les options de mise à jour](mises-a-jour.md) couvrent les modes manuel et automatique.

## Référence

- [Configuration et versions épinglées](configuration.md)
- [Organisation du dépôt](organisation.md)
- [Versionnement](versionnement.md)
- [Consignes de contribution](AGENTS.fr.md)

Basé sur [MultiLoader-Template](https://github.com/jaredlll08/MultiLoader-Template)
de jaredlll08 pour la prise en charge de Fabric, Forge et NeoForge.
