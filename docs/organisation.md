# Organisation du dépôt

- `common/` : sources et ressources partagées.
- `fabric/`, `forge/`, `neoforge/` : implémentations des modloaders.
- `minestom/` : application serveur indépendante, avec `settings.gradle`,
  `build.gradle` et son wrapper Gradle 9 pour Java 25.
- Dans chaque module : `src/main/java/` pour le code,
  `src/main/resources/` pour les ressources et `src/test/java/` pour les tests.
- `buildSrc/src/main/groovy/` : conventions Gradle partagées.
- `buildSrc/src/test/groovy/` : tests de l’outillage Gradle et des mises à jour.
- `gradle/wrapper/` : wrapper et version de Gradle.
- `gradle/modules.txt` : liste partagée des modules racine possibles ;
  `gradle/build-plan.gradle` affiche le périmètre avant les tâches du build.
- `.github/workflows/` : compilation et tests dans GitHub Actions.
- `scripts/ci/` : sélection du parcours de CI et contrôles du template ;
  `scripts/ci/tests/` contient les tests de ces outils.
- `docs/` : documentation complémentaire.

`gradle.properties` centralise la version du mod et les versions du jeu et
des dépendances propres à Minecraft. Les scripts `build.gradle` configurent
les modules ; `settings.gradle` lit `gradle/modules.txt` et inclut seulement
les dossiers présents. `common/` reste obligatoire. Les plugins des cibles
absentes ne sont pas chargés inutilement.
Le build Minestom lit ces mêmes propriétés, mais reste séparé du build racine.
Il ne dépend pas de `common/`, dont le code utilise l’API Minecraft vanilla.
Le dossier `common/` reste requis pour la cohérence du template, même
lorsque Minestom est la seule cible conservée.

Les répertoires `build/`, `.gradle/`, `run/` et `runs/` sont générés et ignorés
par Git. Les ressources issues de la génération de données Forge/NeoForge
utilisent les chemins `src/generated/resources/` déclarés par leurs modules.
