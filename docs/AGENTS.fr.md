# Consignes du dépôt

[English](../AGENTS.md) · [Français](AGENTS.fr.md)

Appliquer ces règles aux contributions et aux échanges suivants. Les conserver
lors de la création d’un projet à partir du template.

## Organisation et contrats de build

| Chemin | Responsabilité |
| --- | --- |
| `common/` | Sources, ressources et tests partagés des mods |
| `fabric/`, `forge/`, `neoforge/` | Sources, ressources et tests propres aux modloaders |
| `minestom/` | Serveur autonome avec ses settings et son wrapper |
| `gradle/modules/` | Scripts de build centralisés des cibles |
| `gradle/templates/`, `gradle/bootstrap/` | Fichiers initiaux et initialisation |
| `buildSrc/` | Conventions Gradle et outillage de build |
| `docs/`, `scripts/`, `work/` | Documentation, automatisation et fichiers temporaires |

Conserver Java dans `src/main/java/` de chaque module, les ressources dans
`src/main/resources/`, les tests dans `src/test/java/` et leurs ressources dans
`src/test/resources/`. Les tests partagés vont dans `common/`. Suivre les dossiers
de test vides avec `.gitkeep`. Ne pas créer de `src/`, `resources/` ou `tests/`
globaux à la racine.

Conserver `settings.gradle`, `build.gradle` et `gradle.properties` à la racine.
Centraliser versions, JDK, modules et paramètres de développement dans
`gradle.properties` ; conserver le build d’outillage propre à `buildSrc/`.
Respecter les chemins des ressources générées. Mettre à jour les deux langues
du [guide d’organisation](organisation.md) lors d’un changement d’arborescence.

`common/` est obligatoire. Une cible optionnelle absente est exclue automatiquement.
`modules`, `required_modules` et `standalone_modules` pilotent Gradle et la CI.
Initialiser uniquement les dossiers présents vides ou contenant seulement
`.gitkeep`, depuis `gradle/templates/`. Ne jamais recréer une cible absente ni
écraser un fichier existant pendant l’initialisation.

Conserver des builds séparés : Java 21 / Gradle 8 pour les mods, Java 25 / Gradle 9
pour Minestom. Le source set Minestom compile seulement `Constants`, `CommonClass`
et `PlatformContext` du package `group` configuré dans `common/`. Garder ces trois
classes indépendantes du moteur ; ne charger ni le build NeoForm de common ni
ses ressources de mixins dans Minestom. Le reste de common peut utiliser les API
Minecraft vanilla.

Les quatre cibles transmettent explicitement `PlatformContext` à
`CommonClass.init`. Les appels aux API des modloaders restent dans leurs modules.
La recherche de mods Minestom retourne toujours `false` ; son indicateur de
développement est explicite, désactivé par défaut. La tâche Gradle `run` lit
`minestom_development`.

Configurer Java explicitement. Distinguer la JVM de Gradle des toolchains de
compilation ; ne pas déduire Java des métadonnées ou du bytecode.

Garder `README.md` et `AGENTS.md` comme entrées anglaises à la racine. Leurs
versions françaises vont dans `docs/`. Les autres guides restent dans `docs/`,
avec leurs équivalents français/anglais et des liens de bascule réciproques.
Synchroniser les changements techniques entre traductions. Les configurations
et licences restent aux emplacements attendus par les outils.

Conserver les sorties de build dans `build/`. Ignorer `.gradle/`, `run/`, `runs/`
et les fichiers temporaires. Ne jamais commiter de secrets. Préserver les
modifications existantes de l’utilisateur.

## Branches et commits

Garder une fonctionnalité, ses correctifs, tests, docs et ajustements de CI sur
une seule branche jusqu’à livraison. Utiliser un nom descriptif préfixé par
`feat/`, `fix/`, `refactor/`, `docs/`, `test/`, `build/`, `ci/` ou `chore/` ; ne pas
le préfixer par le nom d’un agent.

Écrire des commits ciblés au format `type(scope): subject`, avec portée
facultative et les mêmes types que les branches. **Titres et descriptions des
commits doivent être exclusivement en anglais.** Séparer les changements
indépendants et conserver les commits thématiques lors d’une fusion, sauf
demande contraire.

Utiliser l’identité de l’agent pour l’auteur et le committer. Avant chaque commit,
vérifier l’origine de `user.name` et `user.email`, puis exécuter
`git var GIT_AUTHOR_IDENT` et `git var GIT_COMMITTER_IDENT`. Corriger la
configuration locale si nécessaire. Ne pas reprendre une identité personnelle
héritée ni modifier la configuration Git globale de l’utilisateur.

## Validation

Exécuter **toutes les compilations et tous les tests automatisés dans GitHub
Actions**, jamais localement dans l’environnement de l’agent. Adapter les
workflows aux technologies et cibles présentes ; conserver rapports et artefacts.

- Le mode template utilise `repository.is_template` de GitHub : code et rapports
  de tests applicatifs peuvent être absents. Valider configuration et outillage.
- Le mode projet compile les cibles présentes et exige tests exécutés et artefacts.
  Une suite absente, vide ou entièrement ignorée ne vaut pas validation.
- Les tests de CI vont dans `scripts/ci/tests/`. Les intégrations Gradle dans
  `scripts/ci/integration/` utilisent des fixtures isolées pour l’initialisation,
  les builds centralisés, le cache de configuration et les contrats Java partagés.
  Les fixtures common et Minestom ne résolvent ni ne lancent les moteurs du jeu ;
  elles ne valident pas les artefacts applicatifs complets.

Avant un build, annoncer les modules à compiler, les cibles absentes et les cibles
présentes non sélectionnées. Afficher le même bilan dans les logs Gradle et la
synthèse Actions, y compris avec réutilisation du cache de configuration.

Vérifier les résultats du commit exact. Distinguer réussites, échecs, tests ignorés
et non exécutés. Ne pas affaiblir les assertions ni désactiver un contrôle pour
obtenir une CI verte. Séparer preuves automatisées et essais manuels ; ne jamais
annoncer un test non réalisé. Signaler toute validation bloquée par l’accès GitHub
ou une erreur d’exécution.

Avant d’approuver le template, vérifier les versions actives dans les métadonnées
officielles de publication. Ce contrôle en lecture seule ne doit ni modifier les
versions ni télécharger de JAR, ZIP ou autre binaire, même partiellement. Conserver
les URL sources. Distinguer version absente et erreur réseau ; les deux bloquent
l’approbation. Une publication ne prouve pas la compatibilité des API.

## Versionnement

Appliquer Semantic Versioning 2.0.0 : PATCH pour un correctif compatible, MINOR pour
une fonctionnalité compatible, MAJOR pour une rupture d’API publique. Évaluer la
branche entière par rapport à la dernière version normale livrée ; ne pas
incrémenter à chaque commit ni automatiquement pour des docs, tests ou changements
de CI. `0.y.z` reste instable ; le nombre de fonctionnalités ne justifie pas `1.0.0`.

Centraliser la version du produit dans `gradle.properties`. Ne pas réutiliser un
numéro d’artefact distribué pour un contenu différent. Choisir une version Minestom
publiée pour le `minecraft_version` exact, sans dernière version globale ni
sélecteur dynamique. Voir [le versionnement](versionnement.md).

Les préversions sont autorisées sur les branches de travail. Sur `main`, la version
du produit doit être exactement `MAJOR.MINOR.PATCH` : trois entiers sans zéro
initial, préfixe, suffixe de préversion ou métadonnée de build. Avant une fusion
autorisée :

1. Promouvoir la version normale sur la branche de travail.
2. Obtenir une CI réussie pour ce commit exact.
3. Fusionner le commit testé sans changer ensuite sa version sur `main`.

## Validation utilisateur et fusion

La déclaration explicite **« le travail est terminé »** de l’utilisateur valide
sa revue de la branche courante et autorise sa fusion dans la branche principale,
puis la suppression des branches de travail locale et distante après réussite.
Citer cette phrase dans une question ou une instruction ne vaut pas autorisation.
Une CI verte seule ne vaut pas validation utilisateur. Avant une fusion autorisée,
vérifier les contrôles courants, résoudre les conflits et signaler les blocages réels.

## Documentation et communication

S’adresser à des développeurs, y compris juniors. Commencer par l’action ou le
résultat technique, fournir commandes et exemples concrets, et expliquer brièvement
les termes peu familiers. Supprimer répétitions, historique de conversation et
remplissage. Garder les contraintes et limites de validation explicites.

À la première utilisation du template, documenter objectif, technologies, cibles,
organisation et validation du projet. Ne pas inventer licence ou visibilité.
Ne pas présenter un contrôle générique comme un build ou un test du produit.
Appliquer les préférences enregistrées sans les redemander. Distinguer propositions,
changements réalisés, résultats validés et contrôles restants.
