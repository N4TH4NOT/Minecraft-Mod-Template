[English](minestom.md) | [Français](minestom.fr.md)

# Minestom for Minecraft 1.21.10

`minestom/` is a standalone server: it uses its own engine and does not
load Fabric, Forge or NeoForge mods. It requires **Java 25** and its own
**Gradle 9.1.0** wrapper. The mod build keeps Java 21 and Gradle 8.

The pinned dependency is `net.minestom:minestom:2025.12.19-1.21.10`.
Choose a release published for the project's `minecraft_version`, rather
than the latest Minestom release overall: the build checks this suffix.
Java 25 has been required since the [first Minestom release for 1.21.10](https://github.com/Minestom/Minestom/releases/tag/2025.10.11-1.21.10).

## Configuration and build

Settings live in [`gradle.properties`](../gradle.properties):
`minestom_version`, `minestom_java_version`, `minestom_gradle_version`,
`minestom_main_class` and `minestom_development`. Minestom appears in both
`modules` and `standalone_modules`; its central build script is
`gradle/modules/minestom.gradle`.

In project mode, GitHub Actions builds this target from the repository root:

```sh
./minestom/gradlew -p minestom --no-daemon --stacktrace build
```

Use the ZIP/TAR distribution produced in `minestom/build/distributions/`:
it includes the launch scripts and their dependencies. The JAR alone is
not enough to run the server.

## Provided example

`MinestomServer` creates a flat world and a spawn point. From the extracted
distribution, with a JDK 25:

```sh
./bin/modid-minestom-1.21.10 127.0.0.1 25565
```

The script name comes from `mod_id` and `minecraft_version`. With no
arguments, the example listens on `127.0.0.1:25565`. It uses `Auth.Offline()`
for local development; choose the future server's authentication mode
before exposing it to a network. On Windows, use the matching `.bat` script.

The example calls `CommonClass.init(context)`, as the three modloaders do.
Its `PlatformContext` contains the name `Minestom` and the selected
development mode; `context.isModLoaded().test(id)` always returns `false`,
because Minestom does not load mods. Read the context through
`server.platformContext()`.

`start(host, port, development)` selects the mode explicitly; the two-argument
overload uses `false`. For the Gradle `run` task:

```sh
./minestom/gradlew -p minestom run -Pminestom_development=true
```

The `main` entrypoint reads the `template.development` JVM property,
disabled by default. In a distribution:

```sh
JAVA_OPTS='-Dtemplate.development=true' ./bin/modid-minestom-1.21.10
```

## Shared code and tests

This build compiles only three engine-independent sources from `common/`:
`Constants`, `CommonClass` and `PlatformContext`, in the package configured by `group`.
It does not load the `common/` build, NeoForm or mixin resources. Other
classes in `common/` may use vanilla Minecraft.

In template mode, CI checks the configuration and an isolated test project
compiles these three classes without the Minestom engine. In project mode,
the JUnit test starts the real server on an ephemeral local port: context,
chunk generation, Minecraft status, ping/pong and shutdown. The server is
closed even when an assertion fails.

See [validation](validation.md), [development](developpement.md)
and the [contribution instructions](../AGENTS.md). Back to the [overview](../README.md).
