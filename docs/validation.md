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

Les tests Python des scripts de CI vérifient notamment la sélection du
parcours, l’acceptation d’un template sans sources, ainsi que le refus de
rapports de projet absents ou sans test exécuté. Ces contrôles ne sont pas
présentés comme une compilation ou un essai de démarrage du produit.

## Parcours projet

La matrice est construite à partir des cibles configurées dans le dépôt.
Une cible retirée de la configuration ne doit plus rester dans une matrice
codée en dur. Le build autonome Minestom est détecté séparément du build
multi-module des mods.

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
