[English](mises-a-jour.en.md) | **Français**

# Mise à jour des dépendances des mods

Ces tâches conservent `minecraft_version` et recherchent les dernières versions
stables compatibles pour :

| Composants | Propriétés modifiées |
| --- | --- |
| Fabric | `fabric_loader_version`, `fabric_version` |
| Forge et NeoForge | `forge_version`, `neoforge_version`, `neo_form_version` |
| Mappings | `parchment_minecraft`, `parchment_version` |
| Configuration et interface | `cloth_config_version`, `modmenu_version` |

Elles ne modifient ni la version du produit, ni Java, Gradle, ses plugins ou
Minestom. Le build autonome Minestom n’exécute pas cet outil.

## Consulter puis appliquer

Depuis la racine du dépôt :

```sh
./gradlew checkModUpdates
./gradlew updateModVersions
```

`checkModUpdates` affiche les changements sans écrire. `updateModVersions`
les applique à `gradle.properties`. Dans IntelliJ, les deux tâches sont sous
**Gradle → Tasks → mod development** ; recharger le projet Gradle après une mise
à jour manuelle.

Exécuter ces tâches séparément d’une construction : les modules sont déjà
configurés quand une tâche manuelle s’exécute. Pour construire avec les nouvelles
versions dans la même invocation CI, utiliser le mode automatique.

## Activer le mode automatique

`autoUpdateModVersions` est désactivé par défaut.

Dans **Actions → Validate template or build project → Run workflow**, choisir
`repository_type=project` et activer `update_mod_versions`. La CI transmet
`-PautoUpdateModVersions=true` et désactive le cache de configuration. Elle
conserve le `gradle.properties` utilisé dans les rapports ; elle ne committe
ni ne pousse les changements.

Le switch Gradle accepte uniquement `true` ou `false`. Il peut être défini avec :

- `-PautoUpdateModVersions=true` dans les arguments Gradle ;
- `ORG_GRADLE_PROJECT_autoUpdateModVersions=true` dans l’environnement ;
- `autoUpdateModVersions=true` dans `gradle.properties`.

Une valeur explicite du fichier prime sur la variable d’environnement ;
`-PautoUpdateModVersions=false` permet de désactiver temporairement le mode.
Une ligne commentée ne masque pas la variable d’environnement.

Le mode automatique consulte les dépôts et actualise les propriétés en mémoire
**avant la configuration des modules**. Il s’applique aux constructions, tests
et tâches personnalisées. L’aide, l’inspection des dépendances, `clean` seul,
les tâches manuelles de mise à jour et une synchronisation IntelliJ sans tâche
ne le déclenchent pas.

Il exige le réseau et `--no-configuration-cache` : le cache ne doit pas empêcher
une nouvelle consultation à chaque invocation. Le mode hors ligne est refusé.
L’option CI est sans effet en mode `template` et pour Minestom. Les compilations
et tests restent réservés à GitHub Actions selon les [consignes](AGENTS.fr.md).

## Sélection et protection du fichier

Fabric API, Forge, NeoForge et NeoForm sont filtrés pour la version exacte du jeu.
Fabric Loader est choisi parmi les versions stables publiées. Cloth Config et
Mod Menu doivent déclarer la compatibilité avec Minecraft et Fabric sur Modrinth,
et leur version doit aussi exister sur le dépôt Maven du projet.

Parchment privilégie la version exacte de Minecraft. Si les mappings n’existent
pas, seul le précédent `parchment_minecraft` configuré peut être conservé, avec
ses derniers mappings stables. Une erreur réseau ne vaut pas absence. Les versions
alpha, bêta, RC et SNAPSHOT sont exclues.

Une version locale stable supérieure à la dernière version compatible publiée
provoque un arrêt explicite. Vérifier alors la configuration et les métadonnées ;
l’outil ne rétrograde pas et ne conserve pas silencieusement une version non vérifiée.

Toutes les recherches doivent réussir avant l’écriture. Les commentaires,
l’ordre, les espaces et les autres paramètres sont conservés. Le remplacement
est atomique ; une modification concurrente détectée arrête l’opération sans
écraser le travail existant.

## Réseau et validation

Les requêtes HTTPS gardent la vérification TLS et les paramètres proxy Java/Gradle.
Aucun token n’est nécessaire. Autoriser ces hôtes dans l’environnement d’exécution :
`maven.fabricmc.net`, `maven.minecraftforge.net`, `maven.neoforged.net`,
`maven.shedaniel.me`, `maven.terraformersmc.com` et `api.modrinth.com`.

Une erreur HTTP ou des métadonnées invalides interrompent l’opération sans modifier
`gradle.properties`. La CI teste le résolveur, le switch et l’écriture avec des
fixtures sans réseau, puis conserve leurs rapports. Toute nouvelle version doit
encore passer les builds et tests des cibles concernées : l’existence d’une
publication ne garantit pas la compatibilité de son API.

Voir la [validation CI](validation.md), le [versionnement](versionnement.md)
et le [README](README.fr.md).
