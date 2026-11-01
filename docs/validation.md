**English** | [Français](validation.fr.md)

# Validation

Run all builds and automated tests in **GitHub Actions**, as required by the
[repository instructions](../AGENTS.md).

## Choose the CI path

In GitHub, open **Actions → Validate template or build project → Run workflow**.
Select the branch and set `repository_type`:

| Mode | Purpose |
| --- | --- |
| `auto` | Uses GitHub’s `repository.is_template` field. A repository created through “Use this template” normally follows the project path. |
| `template` | Validates the scaffold, including when application Java sources are absent. |
| `project` | Builds and tests the targets that are present. Also checks the template examples without changing the repository’s GitHub template status. |

Check the **mode** and **commit SHA** in the results. A successful template run
does not validate the applications covered by the project path.

## Check the scope before compilation

Gradle and CI read `modules`, `required_modules` and `standalone_modules` from
`gradle.properties`. `common/` is required; removing a target directory, such as
`forge/`, excludes it. Retain at least one application target. Minestom keeps
its standalone build and wrapper.

Logs and the CI summary distinguish absent directories, present targets and
planned compilations. Gradle also runs `reportBuildPlan` before its other tasks,
including when the configuration cache is reused. A planned task may later be
avoided because its outputs are up to date or restored from the build cache.

An existing target directory that is empty or contains only `.gitkeep` is initialized from the presets.
Project CI runs this bootstrap before building; template validation checks the
presets without modifying application directories.

## Template checks

The template path checks properties, central build scripts, presets, resources
and wrappers. Resource placeholders are expected; application test suites and
application Java code are optional.

CI also checks the supporting tooling:

- Python tests cover CI decisions and reject missing or empty project test reports.
- Gradle fixtures check initialization, file preservation, idempotence and scope reporting with the configuration cache.
- One fixture compiles the generated common classes and tests the `PlatformContext` contract without resolving or starting Minecraft or a modloader.
- A Minestom fixture compiles the three selected neutral Java classes from `common/` without loading its NeoForm project, mixin resources or the Minestom engine.

These fixtures check the scaffold and shared API. They do not replace full
application builds or tests.

The **Test Gradle scaffolding and generated shared context** job summary lists
each fixture as `✅ Passed`, `❌ Failed` / `Error` or `⏩ Skipped`.
The `scaffold-integration` artifact retains logs and a JSON report with exception
tracebacks.

## Published version checks

**Verify configured versions in official repositories** runs before template
validation and application builds. It reads fixed versions from
`gradle.properties` for declared targets that are present, including empty
directories awaiting initialization. Absent targets are excluded.

The check reads official text metadata only: Maven POMs, plugin marker POMs,
Minecraft’s version manifest JSON, and Gradle distribution SHA-256 values.
**It downloads no JAR, ZIP or other binary, including partial downloads.**
It does not resolve transitive dependencies or select versions or Java installations.

The future product version, Java settings and Minecraft format numbers are
handled separately from published dependency versions. An unknown version
property, dynamic selector or mutable SNAPSHOT cannot be silently approved.

A missing version or invalid metadata fails the check. A network problem means
“unverified,” never “version missing” or “validated,” and also blocks approval.
Network retries are bounded; previous verification results are not reused from disk.

The **published-versions** artifact retains the JSON report, requested URLs,
exclusions and failure reasons. Unit tests use simulated responses; the job
queries real repositories. A published version alone does not prove application
API compatibility.

Each published version property appears once: in its module's table, or in
**Shared dependencies** when used by multiple active modules. For example,
`mixinextras_version` stays a single shared row. Minestom's Gradle distribution
belongs to Minestom; root tooling stays separate.
The product version, Java settings, parameters without publication checks and
inactive dependencies are omitted from tables. The complete JSON and
configuration diagnostics remain available.

## Project checks

CI installs the declared JDKs for the Gradle runtime, `buildSrc` and compiler
toolchains. Implicit toolchain detection and downloads are disabled. Wrapper
versions and SHA-256 values must match the configuration.

| Target | Checks |
| --- | --- |
| Fabric, Forge, NeoForge | Compilation, `common/` and loader tests, processed resources, entrypoints and artifacts. These tests do not start Minecraft. |
| Minestom | Standalone build, context passed to shared code, real server startup and shutdown, world generation, network protocol and distribution. |

After initialization, a project must contain code to compile. Every expected
application suite must produce reports with **at least one executed test**,
excluding skipped tests. An empty suite proves nothing. Failures remain visible;
reports are retained on failure, and artifacts are required after a successful build.

The manual `update_mod_versions` option applies only to mod builds in `project`
mode. See [dependency updates](mises-a-jour.md) and
[configuration](configuration.md). Return to the [README](../README.md).
