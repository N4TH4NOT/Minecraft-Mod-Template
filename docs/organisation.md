# Organisation du dépôt

- `common/` : sources et ressources partagées.
- `fabric/`, `forge/`, `neoforge/` : implémentations des modloaders.
- Dans chaque module : `src/main/java/` pour le code,
  `src/main/resources/` pour les ressources et `src/test/java/` pour les tests.
- `buildSrc/src/main/groovy/` : conventions Gradle partagées.
- `buildSrc/src/test/groovy/` : tests de l’outillage Gradle et des mises à jour.
- `gradle/wrapper/` : wrapper et version de Gradle.
- `.github/workflows/` : compilation et tests dans GitHub Actions.
- `docs/` : documentation complémentaire.

`gradle.properties` centralise la version du mod et les versions du jeu et
des dépendances propres à Minecraft. Les scripts `build.gradle` configurent
les modules ; `settings.gradle` déclare leurs inclusions et les dépôts de plugins.

Les répertoires `build/`, `.gradle/`, `run/` et `runs/` sont générés et ignorés
par Git. Les ressources issues de la génération de données Forge/NeoForge
utilisent les chemins `src/generated/resources/` déclarés par leurs modules.
