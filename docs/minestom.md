# Serveur Minestom pour Minecraft 1.21.10

`minestom/` est une base d’application serveur autonome. Minestom possède
son propre moteur et sa propre API : il ne charge pas les mods des autres
cibles et ne fournit pas les classes `net.minecraft` utilisées dans `common/`.
Son sourceSet compile une sélection explicite de trois classes neutres de
`common/` : `Constants`, `CommonClass` et `PlatformContext`, dans le package
défini par `group`. Le build `common/`, NeoForm et les ressources de mixins
restent réservés aux mods ; ils ne sont pas inclus dans ce build autonome.

## Versions et construction

La dépendance est `net.minestom:minestom:2025.12.19-1.21.10`, publiée dans
Maven Central. La [première version Minestom pour Minecraft 1.21.10](https://github.com/Minestom/Minestom/releases/tag/2025.10.11-1.21.10)
exige déjà Java 25. Le [tag retenu](https://github.com/Minestom/Minestom/releases/tag/2025.12.19-1.21.10)
conserve cette cible du jeu.

Sélectionner la dernière version publiée pour le `minecraft_version`
du projet, pas la dernière version générale de Minestom. Les
[métadonnées Maven Central](https://repo.maven.apache.org/maven2/net/minestom/minestom/maven-metadata.xml)
publient les versions avec leur suffixe Minecraft. La version retenue
est la dernière de la série `-1.21.10` ; aucun sélecteur `latest.release`
n’est utilisé.

Les propriétés `minestom_version` et `minestom_java_version`, ainsi que
l’identité et la version du projet, sont centralisées dans le
`gradle.properties` racine. Le build vérifie que le suffixe Minecraft de
la dépendance correspond à `minecraft_version`. L’outil de mise à jour
des modloaders laisse ces propriétés Minestom inchangées.

Le wrapper du dossier `minestom/` fournit Gradle 9.1.0. Le wrapper racine
reste sous Gradle 8 pour Forge. Minestom est déclaré dans `modules` et
`standalone_modules` : les deux builds utilisent des chaînes distinctes.
Son script est `gradle/modules/minestom.gradle`.
Dans GitHub Actions, le parcours projet lance depuis la racine :

```sh
./minestom/gradlew -p minestom --no-daemon --stacktrace build
```

Le plugin `application` fournit les distributions ZIP/TAR, les scripts de
lancement et leurs dépendances. Le JAR seul ne contient pas Minestom et
ses dépendances. La distribution porte le nom
`modid-minestom-1.21.10`, dérivé de `mod_id` et `minecraft_version`.

## Exemple fourni

`MinestomServer` initialise un monde plat, raccorde les joueurs à cette
instance et définit leur point d’apparition. Ce code illustre le démarrage
et l’arrêt ; il ne constitue pas une fonctionnalité métier du futur dépôt.

Il appelle aussi `CommonClass.init(context)`, comme les trois modloaders.
Le contexte porte le nom `Minestom`, le mode de développement fourni au
démarrage et un prédicat qui retourne toujours `false` pour la recherche
de mods. Le contexte est accessible par `server.platformContext()`.

L’appel Java `start(host, port, development)` choisit explicitement ce mode ;
`start(host, port)` utilise `false`. Le point d’entrée `main` lit la propriété
Java `template.development`, désactivée par défaut. Pour la tâche Gradle
`run`, `minestom_development=false` est centralisé dans `gradle.properties` :

```sh
./minestom/gradlew -p minestom run -Pminestom_development=true
```

Le script de la distribution démarre par défaut sur `127.0.0.1:25565`.
Il accepte une adresse et un port en arguments. Exemple après extraction
de la distribution et avec un JDK 25 :

```sh
./bin/modid-minestom-1.21.10 127.0.0.1 25565
```

Pour activer le contexte de développement dans une distribution :

```sh
JAVA_OPTS='-Dtemplate.development=true' ./bin/modid-minestom-1.21.10 127.0.0.1 25565
```

Les trois classes sélectionnées restent indépendantes des API de moteur.
Pour en partager d’autres avec Minestom, adapter explicitement la sélection
dans `gradle/modules/minestom.gradle` et conserver cette indépendance.
Les autres classes de `common/` peuvent continuer à utiliser Minecraft vanilla.

L’exemple utilise `Auth.Offline()` pour le développement local. Le futur
serveur choisira son mode d’authentification avant une ouverture au réseau.

## Test de fonctionnement

Le test JUnit démarre le vrai moteur sur l’interface locale avec un port
attribué par le système. Il vérifie la génération d’un chunk, le format
de la réponse status Minecraft, un échange ping/pong, le contexte transmis
au code commun et l’arrêt du serveur.
Les opérations réseau et le test ont des délais limites. Le serveur est
fermé même lorsqu’une assertion échoue.

Ce test s’exécute dans GitHub Actions en mode projet. En mode template,
la CI contrôle la configuration et accepte que l’exemple et ses tests
applicatifs soient absents. Une fixture isolée vérifie aussi la compilation
des trois classes partagées dans le build Minestom, sans dépendance au
moteur Minestom. Voir [les parcours de validation](validation.md).
