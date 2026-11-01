[English](organisation.md) | [Français](organisation.fr.md)

# Organisation du dépôt

Commencer par le [README](README.fr.md) et les [consignes](AGENTS.fr.md).
Ce tableau indique où modifier chaque partie du projet.

| Chemin | Quand le modifier |
| --- | --- |
| `common/` | Partager du code entre les mods ; ce module est obligatoire et peut utiliser Minecraft vanilla |
| `fabric/`, `forge/`, `neoforge/` | Ajouter une intégration propre à un modloader |
| `minestom/` | Développer le serveur autonome et son démarrage |
| `<module>/src/main/java/` | Écrire le code de la cible |
| `<module>/src/main/resources/` | Modifier ses ressources et métadonnées |
| `<module>/src/test/java/`, `<module>/src/test/resources/` | Ajouter ses tests et leurs données |
| `gradle.properties` | Changer les modules, l’identité, les versions, les JDK ou les paramètres |
| `settings.gradle`, `gradle/modules/` | Modifier la sélection des modules et les builds centraux |
| `buildSrc/src/main/groovy/`, `buildSrc/src/test/groovy/` | Adapter et tester les conventions Gradle ou l’outil de mise à jour |
| `gradle/templates/` | Modifier les exemples générés dans les dossiers vides |
| `gradle/bootstrap/` | Adapter l’initialisation sans construire les applications |
| `gradle/build-plan.gradle` | Modifier le bilan des compilations prévues |
| `gradle/wrapper/`, `minestom/gradle/wrapper/` | Synchroniser les wrappers et leurs scripts de lancement |
| `.github/workflows/`, `scripts/ci/` | Adapter la CI et ses contrôleurs ; tests dans `tests/` et fixtures dans `integration/` sous `scripts/ci/` |
| `docs/` | Maintenir les guides et leurs traductions |

Les builds centraux conservent les chemins `src/` et `build/` relatifs au
module. Minestom utilise son propre build et une sélection limitée de
sources neutres de `common/` ; voir [le guide de développement](developpement.fr.md).

Un dossier cible absent reste exclu. Un dossier déclaré vide, ou avec
`.gitkeep` seul, est initialisé depuis son preset. Les dossiers non vides
sont conservés ; `common/` doit toujours exister.

Les sorties `build/`, les caches `.gradle/` et les dossiers d’exécution
`run/` et `runs/` sont ignorés. Les ressources issues de la génération de
données utilisent `generated_resources_directory`, par défaut `src/generated/resources/`.

Voir [la validation](validation.fr.md) pour les contrôles du template et les
constructions des projets dérivés.
