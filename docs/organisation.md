# Organisation du dépôt

- `common/` : sources et ressources partagées.
- `fabric/`, `forge/`, `neoforge/` : implémentations des modloaders.
- `minestom/` : application serveur indépendante, avec `settings.gradle`,
  son wrapper Gradle et ses sources ; son build est centralisé avec les autres.
- Dans chaque module : `src/main/java/` pour le code,
  `src/main/resources/` pour les ressources et `src/test/java/` pour les tests.
- `buildSrc/src/main/groovy/` : conventions Gradle partagées.
- `buildSrc/src/test/groovy/` : tests de l’outillage Gradle et des mises à jour.
- `gradle/wrapper/` : wrapper et version de Gradle.
- `gradle/modules/` : scripts de build de chaque cible.
- `gradle/templates/` : sources, ressources, tests et fichiers de démarrage
  utilisés uniquement pour initialiser les dossiers vides.
- `gradle/bootstrap/` : point d’entrée pour initialiser sans configurer les applications.
- `gradle/build-plan.gradle` : bilan du périmètre avant les tâches du build.
- `.github/workflows/` : compilation et tests dans GitHub Actions.
- `scripts/ci/` : sélection du parcours de CI et contrôles du template ;
  `scripts/ci/tests/` contient leurs tests unitaires et `scripts/ci/integration/`
  leurs tests avec Gradle sur des fixtures sans code applicatif.
- `docs/` : documentation complémentaire.

`gradle.properties` centralise les modules, les versions, les JDK et les
paramètres de développement. `settings.gradle` sélectionne les dossiers
présents et associe leur véritable script de build dans `gradle/modules/`.
Les chemins `src/` et `build/` restent relatifs au dossier de chaque module.
`common/` reste obligatoire. Les plugins des cibles
absentes ne sont pas chargés inutilement.
Le build Minestom lit ces mêmes propriétés, mais reste séparé du build racine.
Il ne dépend pas de `common/`, dont le code utilise l’API Minecraft vanilla.
Le dossier `common/` reste requis pour la cohérence du template, même
lorsque Minestom est la seule cible conservée.

Les répertoires `build/`, `.gradle/`, `run/` et `runs/` sont générés et ignorés
par Git. Les ressources issues de la génération de données Forge/NeoForge
utilisent les chemins `src/generated/resources/` déclarés par leurs modules.
