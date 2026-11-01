[English](organisation.en.md) | [Français](organisation.md)

# Repository layout

Start with the [README](../README.md) and [contribution rules](../AGENTS.md).
This table shows where to change each part of the project.

| Path | When to change it |
| --- | --- |
| `common/` | Share code between mods; this required module can use vanilla Minecraft |
| `fabric/`, `forge/`, `neoforge/` | Add a modloader-specific integration |
| `minestom/` | Develop the standalone server and its startup |
| `<module>/src/main/java/` | Write target code |
| `<module>/src/main/resources/` | Change its resources and metadata |
| `<module>/src/test/java/`, `<module>/src/test/resources/` | Add its tests and test data |
| `gradle.properties` | Change modules, identity, versions, JDKs or settings |
| `settings.gradle`, `gradle/modules/` | Change module selection and central builds |
| `buildSrc/src/main/groovy/`, `buildSrc/src/test/groovy/` | Adapt and test Gradle conventions or dependency update tooling |
| `gradle/templates/` | Change examples generated in empty directories |
| `gradle/bootstrap/` | Adapt initialization without building applications |
| `gradle/build-plan.gradle` | Change the compilation plan report |
| `gradle/wrapper/`, `minestom/gradle/wrapper/` | Synchronize wrappers and their launcher scripts |
| `.github/workflows/`, `scripts/ci/` | Adapt CI and its checks; tests live in `tests/` and fixtures in `integration/` under `scripts/ci/` |
| `docs/` | Maintain guides and their translations |

Central builds keep `src/` and `build/` paths relative to each module.
Minestom uses its own build and a limited selection of engine-independent
sources from `common/`; see the [development guide](developpement.en.md).

A missing target directory stays excluded. A declared empty directory, or
one containing only `.gitkeep`, is initialized from its preset. Nonempty
directories are preserved; `common/` must always exist.

Generated `build/` output, `.gradle/` caches and `run/` or `runs/` runtime
directories are ignored. Generated data resources use
`generated_resources_directory`, which defaults to `src/generated/resources/`.

See the [validation guide](validation.en.md) for template checks and builds
of derived projects.
