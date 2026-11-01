# Mise à jour des versions de modloaders et dépendances

La version `minecraft_version` reste inchangée. Le mécanisme recherche les
dernières versions stables compatibles pour ces propriétés :

- `fabric_loader_version`, `fabric_version` ;
- `forge_version`, `neoforge_version`, `neo_form_version` ;
- `parchment_minecraft`, `parchment_version` ;
- `cloth_config_version`, `modmenu_version`.

Il ne modifie ni la version du mod, ni Java, ni Gradle et ses plugins,
ni les autres paramètres du projet. Ces outils demandent une validation
de compatibilité entre les trois modloaders avant toute mise à niveau.
Le build autonome Minestom conserve ses propres propriétés
`minestom_version` et `minestom_java_version` ; ces tâches ne les modifient pas.

## Déclenchement manuel

Dans IntelliJ, recharger le projet Gradle, puis ouvrir **Gradle → Tasks →
mod development** :

- `checkModUpdates` affiche les versions disponibles sans écrire de fichier ;
- `updateModVersions` applique les changements à `gradle.properties`.

Ces tâches peuvent également être appelées avec le wrapper :

```sh
./gradlew checkModUpdates
./gradlew updateModVersions
```

Après une mise à jour manuelle, recharger le projet Gradle dans IntelliJ.
Ne pas cumuler une tâche manuelle de mise à jour et une construction dans
la même invocation : la configuration des modules a déjà eu lieu à ce stade.
Utiliser le switch automatique pour construire directement avec les nouvelles versions.

## Mise à jour automatique à chaque construction

Le booléen **autoUpdateModVersions** est désactivé par défaut. Pour l’activer,
choisir l’une de ces méthodes :

1. Ajouter `-PautoUpdateModVersions=true` aux arguments de la configuration
   d’exécution Gradle d’IntelliJ ou à l’invocation du wrapper.
2. Définir `ORG_GRADLE_PROJECT_autoUpdateModVersions=true` dans les variables
   d’environnement de cette configuration Gradle.
3. Décommenter `autoUpdateModVersions=true` dans `gradle.properties` pour
   activer le mode sur ce checkout. Le commentaire seul ne masque pas la
   variable d’environnement ; une propriété explicitement définie dans le
   fichier est prioritaire sur cette variable.

Le mécanisme exige `true` ou `false`. Pour ignorer temporairement un mode
activé dans le fichier, passer `-PautoUpdateModVersions=false`.

La résolution et l’écriture se produisent lors de la configuration du
projet racine, **avant celle des modules**. Les valeurs chargées en mémoire
par Gradle sont aussi actualisées : la construction et les tests de la
même invocation utilisent donc les versions nouvellement sélectionnées.
Le mode s’applique aux tâches de construction, aux tests et aux tâches
personnalisées. Les commandes d’aide, l’inspection des dépendances, `clean`
seul et les tâches manuelles de mise à jour ne le déclenchent pas. Une
synchronisation IntelliJ sans tâche de construction ne le déclenche pas.

Ce mode doit reconsulter les sources à chaque invocation. Il refuse donc
le cache de configuration et le mode hors ligne. Désactiver le cache de
configuration dans la configuration Gradle d’IntelliJ, ou utiliser
`--no-configuration-cache`.

Les compilations et tests de ce dépôt restent réservés à GitHub Actions,
conformément à `AGENTS.md`. Dans le déclenchement manuel du workflow
**Validate template or build project**, activer le booléen **update_mod_versions** pour
transmettre ce switch aux constructions des mods en mode **project**.
Le parcours template ne lance aucune construction applicative et ignore ce
switch. La cible Minestom ne lance pas l’outil de mise à jour des modloaders.
Chaque rapport
conserve aussi le `gradle.properties` utilisé. Le workflow ne committe et
ne pousse aucune mise à jour.

## Sélection et protection des fichiers

Les versions Fabric API, Forge, NeoForge et NeoForm sont filtrées pour la
version exacte de Minecraft. Fabric Loader est sélectionné parmi les
versions stables publiées. Pour Cloth Config et Mod Menu, les déclarations
Modrinth doivent explicitement inclure le jeu ciblé et Fabric ; la version
doit également exister dans le dépôt Maven du projet. Cela évite de choisir
un numéro plus récent destiné à une autre version de Minecraft.

Parchment utilise les mappings de la version exacte du jeu lorsqu’ils
existent. S’ils sont absents, seul le précédent `parchment_minecraft`
configuré peut être conservé, avec ses dernières mappings stables. Une
erreur réseau ne vaut pas absence de mappings. Les versions alpha, beta,
RC et SNAPSHOT sont exclues.

Une version locale stable supérieure à la dernière version compatible
publiée provoque un arrêt explicite, plutôt qu’une rétrogradation ou la
conservation silencieuse d’une version incompatible. Vérifier alors la
version actuelle et les métadonnées des dépôts.

Toutes les résolutions doivent réussir avant l’écriture. Les commentaires,
l’ordre, les espaces et les paramètres sans rapport sont conservés.
Le remplacement du fichier est atomique ; une modification concurrente
détectée provoque un arrêt sans écraser les changements de l’utilisateur.

## Réseau et validation

Les requêtes HTTPS conservent la vérification TLS et les paramètres proxy
de Java/Gradle. Aucun token n’est nécessaire. Les hôtes requis sont :

- `maven.fabricmc.net` ;
- `maven.minecraftforge.net` ;
- `maven.neoforged.net` ;
- `maven.shedaniel.me` ;
- `maven.terraformersmc.com` ;
- `api.modrinth.com`.

Dans l’environnement cloud, autoriser également `api.modrinth.com` dans les
paramètres réseau avant d’utiliser ces tâches : son accès est actuellement
refusé. Une erreur HTTP ou des métadonnées invalides interrompent l’opération
sans modification de `gradle.properties`.

Les tests du résolveur, du switch et de l’écriture utilisent des fixtures
sans accès réseau. Ils sont exécutés explicitement par la CI avec
`./gradlew -p buildSrc test` et leurs rapports sont conservés. Ils ne
garantissent pas qu’une mise à jour de bibliothèque restera compatible au
niveau de toutes ses API : toute nouvelle version doit ensuite passer les
compilations et tests des modloaders dans GitHub Actions.
