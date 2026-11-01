**English** | [Français](mises-a-jour.fr.md)

# Updating mod dependencies

These tasks keep `minecraft_version` unchanged and find the latest compatible
stable releases for:

| Components | Updated properties |
| --- | --- |
| Fabric | `fabric_loader_version`, `fabric_version` |
| Forge and NeoForge | `forge_version`, `neoforge_version`, `neo_form_version` |
| Mappings | `parchment_minecraft`, `parchment_version` |
| Configuration and UI | `cloth_config_version`, `modmenu_version` |

They do not change the product version, Java, Gradle, its plugins or Minestom.
The standalone Minestom build does not run this updater.

## Preview, then apply

From the repository root:

```sh
./gradlew checkModUpdates
./gradlew updateModVersions
```

`checkModUpdates` previews changes without writing. `updateModVersions` applies
them to `gradle.properties`. IntelliJ lists both under **Gradle → Tasks →
mod development**; reload the Gradle project after a manual update.

Run these tasks separately from a build: modules have already been configured
when a manual task executes. To build with newly selected versions in the same
CI invocation, use automatic mode.

## Enable automatic mode

`autoUpdateModVersions` is disabled by default.

In **Actions → Validate template or build project → Run workflow**, select
`repository_type=project` and enable `update_mod_versions`. CI passes
`-PautoUpdateModVersions=true` and disables the configuration cache. Reports
retain the `gradle.properties` used; the workflow commits or pushes no changes.

The Gradle switch accepts only `true` or `false`. Set it through:

- `-PautoUpdateModVersions=true` in Gradle arguments;
- the `ORG_GRADLE_PROJECT_autoUpdateModVersions=true` environment variable;
- `autoUpdateModVersions=true` in `gradle.properties`.

An explicit file value takes precedence over the environment variable.
`-PautoUpdateModVersions=false` temporarily disables automatic mode. A commented
line does not hide the environment variable.

Automatic mode queries repositories and refreshes the in-memory properties
**before module configuration**. It applies to builds, tests and custom tasks.
Help, dependency inspection, `clean` alone, manual update tasks and an IntelliJ
sync without a requested task do not trigger it.

It requires network access and `--no-configuration-cache` so each invocation
queries fresh metadata. Offline mode is rejected. The CI option has no effect
in `template` mode or for Minestom. Builds and tests remain restricted to
GitHub Actions under the [repository instructions](../AGENTS.md).

## Selection and file protection

Fabric API, Forge, NeoForge and NeoForm are filtered for the exact Minecraft
version. Fabric Loader is selected from published stable releases. Cloth Config
and Mod Menu must declare Minecraft and Fabric compatibility on Modrinth, and
the version must also exist in the project’s Maven repository.

Parchment prefers mappings for the exact Minecraft version. If those mappings
are absent, only the previously configured `parchment_minecraft` may be retained,
using its latest stable mappings. A network error is not evidence of absence.
Alpha, beta, RC and SNAPSHOT releases are excluded.

A stable local version newer than the latest compatible published release stops
the operation. Check the configuration and repository metadata; the updater
neither downgrades nor silently retains an unverified version.

All lookups must succeed before writing. Comments, order, spacing and unrelated
settings are preserved. File replacement is atomic; a detected concurrent edit
stops the operation without overwriting existing work.

## Network access and validation

HTTPS requests preserve TLS verification and Java/Gradle proxy settings. No
token is needed. Allow these hosts in the execution environment:
`maven.fabricmc.net`, `maven.minecraftforge.net`, `maven.neoforged.net`,
`maven.shedaniel.me`, `maven.terraformersmc.com` and `api.modrinth.com`.

HTTP errors or invalid metadata stop the operation without changing
`gradle.properties`. CI tests the resolver, switch and file handling with
network-free fixtures and retains their reports. Every newly selected version
must still pass the relevant target builds and tests: publication alone does
not guarantee API compatibility.

See [CI validation](validation.md), [versioning](versionnement.md)
and the [README](../README.md).
