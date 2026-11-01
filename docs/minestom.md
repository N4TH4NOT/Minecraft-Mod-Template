# Serveur Minestom pour Minecraft 1.21.10

`minestom/` est une base d’application serveur autonome. Minestom possède
son propre moteur et sa propre API : il ne charge pas les mods des autres
cibles et ne fournit pas les classes `net.minecraft` utilisées dans `common/`.
Le code métier indépendant d’un moteur pourra être extrait dans une
bibliothèque partagée lorsque le futur projet en aura besoin.

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
reste sous Gradle 8 pour Forge. Ne pas ajouter Minestom aux inclusions du
`settings.gradle` racine : les deux builds utilisent des chaînes distinctes.
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

Le script de la distribution démarre par défaut sur `127.0.0.1:25565`.
Il accepte une adresse et un port en arguments. Exemple après extraction
de la distribution et avec un JDK 25 :

```sh
./bin/modid-minestom-1.21.10 127.0.0.1 25565
```

L’exemple utilise `Auth.Offline()` pour le développement local. Le futur
serveur choisira son mode d’authentification avant une ouverture au réseau.

## Test de fonctionnement

Le test JUnit démarre le vrai moteur sur l’interface locale avec un port
attribué par le système. Il vérifie la génération d’un chunk, le format
de la réponse status Minecraft, un échange ping/pong et l’arrêt du serveur.
Les opérations réseau et le test ont des délais limites. Le serveur est
fermé même lorsqu’une assertion échoue.

Ce test s’exécute dans GitHub Actions en mode projet. En mode template,
la CI contrôle la configuration et accepte que l’exemple et ses tests
applicatifs soient absents. Voir [les parcours de validation](validation.md).
