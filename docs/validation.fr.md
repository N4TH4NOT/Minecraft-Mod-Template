[English](validation.md) | **Français**

# Validation

Toutes les compilations et tous les tests automatisés s’exécutent dans
**GitHub Actions**, selon les [consignes du dépôt](AGENTS.fr.md).

## Choisir le parcours CI

Dans GitHub, ouvrir **Actions → Validate template or build project → Run workflow**.
Sélectionner la branche et la valeur de `repository_type` :

| Mode | Usage |
| --- | --- |
| `auto` | Utilise le champ GitHub `repository.is_template`. Un dépôt créé avec « Use this template » suit normalement le parcours projet. |
| `template` | Valide le modèle, même sans sources Java applicatives. |
| `project` | Compile et teste les cibles présentes. Permet aussi de vérifier les exemples du modèle sans changer le statut GitHub du dépôt. |

Vérifier le **mode** et le **SHA du commit** dans les résultats. Une CI template
réussie ne valide pas les applications du parcours projet.

## Vérifier le périmètre avant la compilation

Gradle et la CI lisent `modules`, `required_modules` et `standalone_modules`
dans `gradle.properties`. `common/` est obligatoire ; supprimer un dossier
cible, par exemple `forge/`, suffit à l’exclure. Garder au moins une cible
applicative. Minestom conserve son build et son wrapper autonomes.

Les logs et la synthèse CI distinguent les dossiers absents, les cibles
présentes et les compilations prévues. Gradle affiche aussi `reportBuildPlan`
avant ses autres tâches, y compris après réutilisation du cache de configuration.
Une tâche planifiée peut ensuite être évitée si ses sorties sont à jour ou
récupérées depuis le cache.

Un dossier cible présent, vide ou contenant seulement `.gitkeep`, est initialisé depuis les presets.
La CI projet lance ce bootstrap avant la construction ; la validation du modèle
vérifie les presets sans modifier les dossiers applicatifs.

## Contrôles du modèle

Le parcours template contrôle les propriétés, scripts centraux, presets,
ressources et wrappers. Les placeholders sont attendus ; aucune suite
applicative ni aucun code Java applicatif n’est exigé.

Les contrôles de l’outillage s’exécutent aussi en CI :

- Les tests Python couvrent les décisions de CI et le refus des rapports de projet absents ou vides.
- Les fixtures Gradle vérifient l’initialisation, la préservation des fichiers, l’idempotence et le bilan avec cache de configuration.
- Une fixture compile les classes communes générées et teste le contrat `PlatformContext`, sans résoudre ni démarrer Minecraft ou un modloader.
- Une fixture Minestom compile les trois classes Java neutres sélectionnées depuis `common/`, sans charger son projet NeoForm, ses ressources de mixins ou le moteur Minestom.

Ces fixtures vérifient le modèle et l’API partagée. Elles ne remplacent pas
la compilation complète ni les tests des applications.

La synthèse du job **Test Gradle scaffolding and generated shared context**
affiche un statut par fixture : `✅ Passed`, `❌ Failed` / `Error`, `⏩ Skipped`.
L’artefact `scaffold-integration` conserve les logs et le rapport JSON avec
les traces d’exception.

## Vérification des versions publiées

Le job **Verify configured versions in official repositories** précède la
validation du modèle et les constructions applicatives. Il lit les versions
fixes de `gradle.properties` pour les cibles déclarées et présentes, y compris
les dossiers vides à initialiser. Les cibles absentes sont exclues.

Il consulte uniquement les métadonnées textuelles officielles : POM Maven,
POM marqueurs des plugins, manifeste JSON des versions Minecraft, et sommes
SHA-256 des distributions Gradle. **Ce contrôle ne télécharge aucun JAR, ZIP
ou autre binaire, même partiellement.** Il ne résout pas les dépendances
transitives et ne choisit aucune version ou installation Java.

La version du futur produit et les paramètres Java ou formats Minecraft sont
traités séparément des versions de dépendances publiées. Une propriété de
version sans règle de vérification, un sélecteur dynamique ou un SNAPSHOT
mutable ne reçoit pas d’approbation silencieuse.

Une version introuvable ou des métadonnées invalides font échouer le contrôle.
Un problème réseau signifie « non vérifié », jamais « version absente » ou
« validé » ; il bloque aussi l’approbation. Les reprises réseau sont limitées,
sans réutilisation d’une ancienne validation sur disque.

L’artefact **published-versions** conserve le rapport JSON, les URLs consultées,
les exclusions et les motifs d’échec. Ses tests utilisent des réponses simulées ;
le job consulte les dépôts réels. Une publication existante ne prouve pas à elle
seule la compatibilité du code applicatif.

## Contrôles d’un projet

La CI installe les JDK déclarés pour le runtime Gradle, `buildSrc` et les
toolchains. La détection et le téléchargement implicites des toolchains sont
désactivés. Les wrappers sont comparés aux versions et SHA-256 configurés.

| Cible | Contrôles |
| --- | --- |
| Fabric, Forge, NeoForge | Compilation, tests de `common/` et du loader, ressources traitées, points d’entrée et artefacts. Les tests ne démarrent pas Minecraft. |
| Minestom | Build autonome, contexte transmis au code partagé, démarrage et arrêt réels du serveur, génération du monde, protocole réseau et distribution. |

Après initialisation, le projet doit contenir du code à compiler. Chaque suite
applicative attendue doit produire des rapports avec **au moins un test exécuté**,
hors tests ignorés. Une suite vide ne valide rien. Les échecs restent visibles ;
les rapports sont conservés même en cas d’échec et les artefacts sont requis après
une construction réussie.

L’option manuelle `update_mod_versions` ne concerne que les builds de mods en
mode `project`. Voir les [mises à jour](mises-a-jour.fr.md) et la
[configuration](configuration.fr.md). Retour au [README](README.fr.md).
