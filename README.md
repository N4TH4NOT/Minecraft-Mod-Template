# Minecraft Mod Template — 1.21.10

[English](README.md) · [Français](docs/README.fr.md)

Multi-target template for Minecraft **1.21.10**. Configure versions, modules and
JDKs in `gradle.properties`; target build scripts live in `gradle/modules/`.

| Target | JDK | Wrapper |
| --- | --- | --- |
| Fabric, Forge, NeoForge | 21 | Root: Gradle 8.14.6 |
| Minestom standalone server | 25 | `minestom/`: Gradle 9.1.0 |

## Set up a project

1. Create a repository with **Use this template**.
2. Set project identity and dependency versions in `gradle.properties`.
3. Keep `common/` and at least one target. Delete optional target directories
   to exclude them from Gradle and CI.
4. To restore a target, create its empty directory, then initialize it:

```sh
mkdir forge
./gradlew -p gradle/bootstrap help
```

Existing files are preserved. Empty directories, including those containing
only `.gitkeep`, receive starter sources, resources and tests. Minestom also
receives its own wrapper. The bootstrap does not compile applications.

## Share code

Fabric, Forge and NeoForge import `common/` directly. All four targets call
`CommonClass.init(PlatformContext)` with a platform name, development flag and
mod lookup callback. Minestom compiles the same three engine-independent
classes: `Constants`, `CommonClass` and `PlatformContext`.

See [development and shared code](docs/developpement.en.md) and
[Minestom startup options](docs/minestom.en.md).

## Validate changes

Builds and automated tests run in **GitHub Actions**.

| Repository mode | Checks |
| --- | --- |
| Template (`is_template=true`) | Structure, configuration, published versions and isolated Gradle fixtures; application sources may be absent |
| Derived project | Builds, executed tests and artifacts for present targets |

The workflow **Validate template or build project** supports `repository_type`
values `auto`, `template` and `project`. It reports compiled, absent and
unselected modules before builds. Version checks use official publication
metadata without downloading dependency binaries.

See [CI checks and limits](docs/validation.en.md). Dependency update tasks
`checkModUpdates` and `updateModVersions` keep Minecraft fixed;
[update options](docs/mises-a-jour.en.md) describe manual and automatic use.

## Reference

- [Configuration and pinned versions](docs/configuration.en.md)
- [Repository layout](docs/organisation.en.md)
- [Versioning](docs/versionnement.en.md)
- [Contribution instructions](AGENTS.md)

Based on [MultiLoader-Template](https://github.com/jaredlll08/MultiLoader-Template)
by jaredlll08 for Fabric, Forge and NeoForge support.
