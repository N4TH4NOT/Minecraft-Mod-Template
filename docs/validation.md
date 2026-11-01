# Validation adaptée à la nature du dépôt

La CI utilise le champ GitHub `repository.is_template` de l’événement,
et non le nom du dépôt ou la présence supposée d’une application. Le dépôt
template actuel est marqué comme tel sur GitHub. Un dépôt créé avec
« Use this template » suit normalement le parcours projet.

## Parcours template

Un modèle peut ne contenir aucun code applicatif. La CI ne lui impose
donc ni classes Java, ni compilation d’application, ni rapports JUnit
applicatifs. Elle contrôle la structure et les fichiers de configuration
nécessaires aux cibles déclarées, les propriétés, les ressources du modèle
et les wrappers. Les placeholders des ressources sont normaux à ce stade.

Les tests unitaires Python des scripts de CI vérifient notamment la sélection du
parcours, l’acceptation d’un template sans sources, ainsi que le refus de
rapports de projet absents ou sans test exécuté. Ces contrôles ne sont pas
présentés comme une compilation ou un essai de démarrage du produit.

Un job distinct exécute le vrai initialiseur Gradle sur des fixtures
temporaires. Il vérifie le rendu des fichiers, l’identité du projet, la
préservation des fichiers existants et l’idempotence. Il configure aussi
deux modules sans sources pour vérifier les scripts centraux et le bilan
avec réutilisation du cache. Aucune application n’est compilée.

## Parcours projet

La matrice est construite à partir de `modules`, `required_modules` et
`standalone_modules` dans `gradle.properties`, également lus par Gradle,
et des dossiers réellement présents. Supprimer `forge/`, par exemple,
suffit à l’exclure. Les autres cibles restent disponibles. `common/` reste
obligatoire. Conserver au moins une cible applicative.

Le build autonome Minestom est détecté séparément du build multi-module
des mods : il figure dans `modules` et `standalone_modules`.

Les JDK installés proviennent des propriétés centrales : runtime de Gradle,
toolchain de chaque cible et JDK de `buildSrc`. La détection et le téléchargement
implicites des toolchains sont désactivés dans les builds de CI. Les wrappers
sont comparés aux versions et aux empreintes SHA-256 déclarées.

Si un dossier présent est vide, la CI indique qu’il sera initialisé. En
mode projet, elle lance le bootstrap avant la construction ; en mode template,
elle vérifie les presets sans modifier les dossiers de l’application.

| Cible | Chaîne | Contrôles applicatifs |
| --- | --- | --- |
| Fabric / Forge / NeoForge | Java 21, wrapper racine Gradle 8 | Compilation, tests partagés et du loader, artefacts |
| Minestom | Java 25, wrapper `minestom/` Gradle 9 | Compilation, démarrage/arrêt et protocole réseau, distribution |

Les tests de métadonnées des mods vérifient les ressources traitées, les
points d’entrée et la découverte des services. Ils ne lancent pas un client
ou serveur Minecraft. Le test Minestom lance réellement le moteur en local.

Un projet sans code à compiler échoue avec une explication. Pour chaque
suite applicative attendue, les rapports doivent exister et compter au
moins un test exécuté, hors tests ignorés. Les échecs ne sont pas masqués.
Les rapports sont conservés même en cas d’échec ; les artefacts doivent
être présents après une construction réussie.

## Bilan avant la construction

Gradle affiche d’abord les modules présents et absents, puis la tâche
`reportBuildPlan` présente les modules ayant des tâches Java de compilation
dans le graphe réellement sélectionné. Elle précède les autres tâches et
s’exécute aussi lorsque le cache de configuration est réutilisé. Minestom
utilise le même rapport avec son build autonome.

Les modules présents sans compilation planifiée sont affichés séparément
des dossiers absents. Une compilation planifiée peut ensuite être évitée
par Gradle si ses sorties sont à jour ou récupérées depuis le cache.
La CI publie le même périmètre avant ses constructions, dans les logs
et dans la synthèse de l’exécution. En mode template, aucune compilation
applicative n’est planifiée.

## Déclenchement manuel

Le workflow **Validate template or build project** propose `repository_type` :

- `auto` utilise le statut GitHub du dépôt ;
- `template` vérifie le modèle sans exiger de code applicatif ;
- `project` force les constructions et tests des cibles présentes.

Le mode `project` permet ainsi de vérifier les exemples fournis dans le
template avant de les réutiliser. Il ne change pas le statut GitHub du
dépôt. L’option `update_mod_versions` concerne uniquement la construction
des mods ; elle est sans effet sur le parcours template et sur Minestom.

Les compilations et tous les tests automatisés s’exécutent uniquement
dans GitHub Actions, conformément aux consignes du dépôt. Une CI du
parcours template réussie ne vaut pas validation des constructions du
parcours projet : vérifier le mode et le SHA du commit dans les résultats.
