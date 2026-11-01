[English](minestom.md) | [Français](minestom.fr.md)

# Minestom pour Minecraft 1.21.10

`minestom/` est un serveur autonome : il utilise son propre moteur et ne
charge pas les mods Fabric, Forge ou NeoForge. Il requiert **Java 25** et
son wrapper **Gradle 9.1.0**. Le build des mods conserve Java 21 et Gradle 8.

La dépendance retenue est `net.minestom:minestom:2025.12.19-1.21.10`.
Choisir une version publiée pour le `minecraft_version` du projet, et non
la dernière version générale : le build vérifie ce suffixe. Java 25 est
requis depuis la [première version Minestom pour 1.21.10](https://github.com/Minestom/Minestom/releases/tag/2025.10.11-1.21.10).

## Configuration et construction

Les paramètres sont dans [`gradle.properties`](../gradle.properties) :
`minestom_version`, `minestom_java_version`, `minestom_gradle_version`,
`minestom_main_class` et `minestom_development`. Minestom figure dans
`modules` et `standalone_modules` ; son script central est
`gradle/modules/minestom.gradle`.

En mode projet, GitHub Actions construit la cible depuis la racine :

```sh
./minestom/gradlew -p minestom --no-daemon --stacktrace build
```

Utiliser la distribution ZIP/TAR produite dans `minestom/build/distributions/` :
elle contient les scripts de lancement et leurs dépendances. Le JAR seul
ne suffit pas à lancer le serveur.

## Exemple fourni

`MinestomServer` crée un monde plat et un point d’apparition. Depuis la
distribution extraite, avec un JDK 25 :

```sh
./bin/modid-minestom-1.21.10 127.0.0.1 25565
```

Le nom du script dépend de `mod_id` et `minecraft_version`. Sans arguments,
l’exemple écoute sur `127.0.0.1:25565`. Il utilise `Auth.Offline()` pour le
développement local ; choisir l’authentification du futur serveur avant
de l’ouvrir au réseau. Sous Windows, utiliser le script `.bat` correspondant.

L’exemple appelle `CommonClass.init(context)`, comme les trois modloaders.
Son `PlatformContext` porte le nom `Minestom` et le mode de développement
choisi ; `context.isModLoaded().test(id)` retourne toujours `false`, puisque
Minestom ne charge pas de mods. Le contexte est accessible par
`server.platformContext()`.

`start(host, port, development)` choisit explicitement ce mode ; la surcharge
à deux arguments utilise `false`. Pour la tâche Gradle `run` :

```sh
./minestom/gradlew -p minestom run -Pminestom_development=true
```

Le point d’entrée `main` lit la propriété JVM `template.development`,
désactivée par défaut. Dans une distribution :

```sh
JAVA_OPTS='-Dtemplate.development=true' ./bin/modid-minestom-1.21.10
```

## Code partagé et tests

Ce build compile uniquement trois sources neutres de `common/` :
`Constants`, `CommonClass` et `PlatformContext`, dans le package défini par
`group`.
Il ne charge pas le build `common/`, NeoForm ou les ressources de mixins.
Les autres classes de `common/` peuvent utiliser Minecraft vanilla.

En mode template, la CI contrôle la configuration et un projet de test isolé
compile ces trois classes sans moteur Minestom. En mode projet, le test
JUnit démarre le vrai serveur sur un port local éphémère : contexte,
génération d’un chunk, réponse de statut Minecraft, ping/pong et arrêt.
Le serveur est fermé même si une assertion échoue.

Voir [la validation](validation.fr.md), [le développement](developpement.fr.md)
et [les consignes](AGENTS.fr.md). Retour à [l’accueil](README.fr.md).
