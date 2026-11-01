[English](developpement.md) | [Français](developpement.fr.md)

# Developing from the template

Edit `gradle.properties` to configure Gradle and CI. See the
[repository layout](organisation.md) to find code and resources.

## Central settings

| Properties | Purpose |
| --- | --- |
| `modules`, `required_modules`, `standalone_modules` | Declared, required and standalone modules |
| `project_name`, `version`, `group`, `mod_*`, `minestom_main_class` | Project identity and initial source identity |
| `java_version`, `<module>_java_version`, `buildsrc_java_version` | Compiler JDKs for modules and build tooling |
| `gradle_java_version`, `minestom_gradle_java_version` | JDK running each Gradle build |
| `gradle_version`, `minestom_gradle_version`, `*_distribution_sha256` | Wrapper versions and checksums |
| Plugin and library versions | Dependencies used by the central scripts |
| `run_*_directory`, `generated_resources_directory`, `java_encoding`, `test_max_heap_size` | Paths, encoding and test memory |
| `minestom_development` | Minestom context development flag, disabled by default |

Choose the identity before generating sources: changing `group` or `mod_id`
later does not rename existing code. See the
[reference versions](configuration.md) and [versioning rules](versionnement.md).

## Add or remove a target

`common/` is required. Deleting `fabric/`, `forge/`, `neoforge/` or `minestom/`
excludes that directory from Gradle and CI, without editing the central
list or recreating the missing directory.

To restore a declared target, create an empty directory, or one containing
only `.gitkeep`, then run from the repository root:

```sh
mkdir forge
./gradlew -p gradle/bootstrap help
```

The bootstrap copies examples from `gradle/templates/` using the configured
identity, without building applications or changing nonempty directories.
Regular Gradle configuration also initializes targets. For an empty Minestom
directory, use this bootstrap first to create its wrapper.

## Shared platform context

All four targets call `CommonClass.init(context)` with a `PlatformContext`:
platform name, development flag and mod lookup predicate. Fabric, Forge and
NeoForge use `common/`, which retains access to vanilla Minecraft.
Minestom compiles only `Constants`, `CommonClass` and `PlatformContext` from
the `group` package. These three classes stay engine-independent; the
`common/` build, NeoForm and mixin resources are not included in Minestom.

Example inside the Fabric entrypoint, with `net.fabricmc.loader.api.FabricLoader` imported:

```java
var loader = FabricLoader.getInstance();
var context = new PlatformContext("Fabric", loader.isDevelopmentEnvironment(),
        loader::isModLoaded);
CommonClass.init(context);
```

Shared code uses `context.isModLoaded().test(modId)`. Calls to modloader APIs
stay in their modules; Minestom's predicate returns `false`. To share more
engine-independent classes, update the selection in
`gradle/modules/minestom.gradle`.

## JDKs and wrappers

The JDK running Gradle may differ from the one compiling the sources.
Defaults: Java 21 and the root Gradle 8 wrapper for mods; Java 25 and the
Gradle 9 wrapper for Minestom. CI installs the declared JDKs. In your IDE,
import the root build for mods and the `minestom/` build separately.

Keep the wrapper scripts and JARs. After changing central versions or
checksums, synchronize the files:

```sh
./gradlew wrapper
./minestom/gradlew -p minestom syncWrapperPreset
```

The second task also synchronizes the Minestom preset. CI rejects differences
from the properties. GitHub Action references remain pinned in the workflow.
Enable development mode with `-Pminestom_development=true` for `run`, or
`JAVA_OPTS='-Dtemplate.development=true'` for a distribution; see the
[Minestom examples](minestom.md).

## Validation

Automated builds and tests run in GitHub Actions; the
[validation guide](validation.md) explains their scope. CI reports the
selected modules and confirms versions through publisher metadata.
The [dependency update guide](mises-a-jour.md) describes the tasks for
finding and applying newer versions. See also the
[contribution rules](../AGENTS.md) and [README](../README.md).
