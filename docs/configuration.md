[English](configuration.md) | [Français](configuration.fr.md)

# Minecraft 1.21.10 configuration

[`gradle.properties`](../gradle.properties) centralizes project identity,
modules, versions and development settings. Target build scripts live in
`gradle/modules/`; sources and build outputs stay in each module's directory.

## Java and Gradle

| Target | JDK | Gradle wrapper |
| --- | --- | --- |
| `common`, Fabric, Forge, NeoForge | 21 | 8.14.6 at the repository root |
| Standalone Minestom | 25 | 9.1.0 in `minestom/` |

`<module>_java_version` selects a target's compiler, falling back to
`java_version`. `gradle_java_version` and `minestom_gradle_java_version`
select the JVM running each build. These are separate roles: changing the
compiler does not automatically change Gradle's runtime JVM.

ForgeGradle 6 requires Gradle below 9. Java 25 needs Gradle 9.1 or newer,
which is why Minestom has a separate build. Wrapper distributions are
protected by the `*_distribution_sha256` properties. Wrapper update tasks
read the central versions; see [development](developpement.md).

## Pinned versions

This branch targets exactly Minecraft **1.21.10**. Mod descriptors exclude
later game versions.

| Dependency | Version |
| --- | --- |
| Fabric Loader | 0.20.1 |
| Fabric API | 0.138.4+1.21.10 |
| Forge | 60.1.18 |
| NeoForge | 21.10.64 |
| NeoForm | 1.21.10-20251010.172816 |
| Parchment | 1.21.10 / 2025.10.12 |
| Cloth Config Fabric | 20.0.149 |
| Mod Menu | 16.0.1 |
| Mixin | 0.8.7 |
| MixinExtras | 0.5.5 |
| Minestom | 2025.12.19-1.21.10 |

| Build plugin | Version |
| --- | --- |
| Fabric Loom | 1.13.6 |
| ModDevGradle | 2.0.148 |
| ForgeGradle | 6.0.54 |
| MixinGradle | 0.7.38 |
| Foojay resolver | 1.0.0 |

Parchment resolves through NeoForge's Maven mirror. MixinExtras bundles
the loader-specific runtime at the same version used for compilation.
Minecraft pack formats are **69** for resources and **88** for data;
`pack.mcmeta` also declares `min_format` and `max_format`.

The `checkModUpdates` and `updateModVersions` tasks keep the Minecraft
version fixed. They leave Java, Gradle, plugins and Minestom unchanged;
see [dependency updates](mises-a-jour.md). For Minestom, choose a release
published for the target game, as described in [its configuration](minestom.md).

## Modules and validation

`modules`, `required_modules` and `standalone_modules` drive both Gradle
and CI. `common/` is required; missing targets are excluded. An empty target
directory, or one containing only `.gitkeep`, is initialized from
`gradle/templates/` without changing populated directories.

All four targets pass a `PlatformContext` to `CommonClass.init`. Minestom
shares only the three engine-independent classes `Constants`, `CommonClass`
and `PlatformContext`; engine APIs stay in their respective targets.

In template mode, CI accepts missing application code and checks the scaffold
and its tools. Project mode compiles the present targets and runs their tests.
Mod metadata tests do not start Minecraft; the Minestom test starts a real
server. Reports are retained, including on failure. See [validation](validation.md).

Maven publishing is optional: set `local_maven_url` only when publishing to
your chosen repository. Builds and tests do not require publishing secrets.

Back to the [overview](../README.md) and [contribution instructions](../AGENTS.md).
