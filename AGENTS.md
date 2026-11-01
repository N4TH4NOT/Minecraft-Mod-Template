# Repository instructions

[English](AGENTS.md) · [Français](docs/AGENTS.fr.md)

Apply these rules to contributions and future exchanges. Keep them when creating
a project from this template.

## Layout and build contracts

| Path | Responsibility |
| --- | --- |
| `common/` | Shared mod sources, resources and tests |
| `fabric/`, `forge/`, `neoforge/` | Loader-specific sources, resources and tests |
| `minestom/` | Standalone server with its own settings and wrapper |
| `gradle/modules/` | Central target build scripts |
| `gradle/templates/`, `gradle/bootstrap/` | Starter files and initialization |
| `buildSrc/` | Gradle conventions and build tooling |
| `docs/`, `scripts/`, `work/` | Documentation, automation and temporary work |

Keep Java in each module's `src/main/java/`, resources in `src/main/resources/`,
tests in `src/test/java/` and test resources in `src/test/resources/`. Shared tests
belong in `common/`. Track empty test directories with `.gitkeep`. Do not add
root-level `src/`, `resources/` or `tests/` directories.

Keep root `settings.gradle`, `build.gradle` and `gradle.properties`. Centralize
versions, JDKs, modules and development settings in `gradle.properties`; keep
`buildSrc/`'s own tooling build. Preserve generated-resource paths. Update both
language versions of [the layout guide](docs/organisation.en.md) when paths change.

`common/` is required. Optional target directories are excluded automatically
when absent. `modules`, `required_modules` and `standalone_modules` drive Gradle
and CI. Initialize only existing empty directories or those containing only
`.gitkeep`, using `gradle/templates/`. Never recreate absent targets or overwrite
existing files during initialization.

Keep mods on Java 21 / Gradle 8 and Minestom on Java 25 / Gradle 9 in separate
builds. The Minestom source set compiles only `Constants`, `CommonClass` and
`PlatformContext` from the configured `group` package in `common/`. Keep these
three classes engine-independent; do not load common's NeoForm build or mixin
resources into Minestom. Other common classes may use vanilla Minecraft APIs.

All four targets pass `PlatformContext` explicitly to `CommonClass.init`.
Loader API calls stay in their target modules. Minestom's mod lookup always
returns `false`; its development flag is explicit and defaults to `false`.
Gradle `run` reads `minestom_development`.

Configure Java versions explicitly. Distinguish Gradle's runtime JVM from
compiler toolchains; do not infer Java versions from metadata or bytecode.

Keep `README.md` and `AGENTS.md` as English entry points at the root. Store their
French versions in `docs/`; other guides remain in `docs/` with English/French
counterparts and reciprocal language links. Keep technical changes synchronized
between translations. Configuration and license files stay where tools expect them.

Keep build outputs in `build/`. Ignore `.gradle/`, `run/`, `runs/` and temporary
files. Never commit secrets. Preserve the user's existing changes.

## Branches and commits

Keep a feature, its fixes, tests, docs and CI adjustments on one branch until
delivery. Use descriptive branch names with `feat/`, `fix/`, `refactor/`, `docs/`,
`test/`, `build/`, `ci/` or `chore/`; do not prefix them with an agent name.

Write focused commits as `type(scope): subject`, with an optional scope and the
same types as branches. **Commit subjects and bodies must be in English only.**
Separate independent changes and retain thematic commits during merges unless
asked otherwise.

Use the working agent's identity for both author and committer. Before each
commit, check the origins of `user.name` and `user.email`, then run
`git var GIT_AUTHOR_IDENT` and `git var GIT_COMMITTER_IDENT`. Correct local
repository configuration if needed. Do not reuse an inherited personal identity
or change the user's global Git configuration.

## Validation

Run **all builds and automated tests in GitHub Actions**, never locally in the
agent environment. Match workflows to actual technologies and present targets;
retain useful reports and artifacts.

- Template mode uses GitHub `repository.is_template`: application code and
  application test reports may be absent. Validate configuration and tooling.
- Project mode builds present targets and requires executed tests and artifacts.
  An absent, empty or entirely skipped suite is not validation.
- CI tooling tests belong in `scripts/ci/tests/`. Gradle integration tests in
  `scripts/ci/integration/` use isolated fixtures for initialization, central
  builds, configuration-cache reuse and shared Java contracts. Their common and
  Minestom fixtures do not resolve or start game engines and do not validate
  complete application artifacts.

Before a build, report modules scheduled for compilation, absent targets and
present targets not selected. Show the same scope in Gradle logs and the Actions
summary, including when the configuration cache is reused.

Check the exact commit's results. Distinguish passed, failed, skipped and
unexecuted checks. Do not weaken assertions or disable checks to get green CI.
Separate automated evidence from manual testing; never claim an unperformed test.
Report any validation blocked by GitHub access or execution failures.

Before approving the template, verify configured active versions against official
publication metadata. This read-only check must not modify versions or download
any JAR, ZIP or other binary, even partially. Preserve source URLs. Distinguish
missing versions from network failures; both block approval. A publication check
does not prove API compatibility.

## Versioning

Use Semantic Versioning 2.0.0: PATCH for compatible fixes, MINOR for compatible
features and MAJOR for public API breaks. Assess the whole branch against the
last normal release; do not bump for every commit or automatically for docs,
tests or CI. `0.y.z` remains unstable; feature counts do not imply `1.0.0`.

Centralize the product version in `gradle.properties`. Never reuse a distributed
artifact version for different content. Select a published Minestom version for
the exact `minecraft_version`, not the latest global release or a dynamic selector.
See [versioning](docs/versionnement.en.md).

Prereleases are allowed on work branches. On `main`, the product version must be
exactly `MAJOR.MINOR.PATCH`: three integers without leading zeros, prefixes,
prerelease suffixes or build metadata. Before an authorized merge:

1. Promote the normal version on the work branch.
2. Obtain successful CI for that exact commit.
3. Merge the tested commit without changing its version afterward on `main`.

## User validation and merging

The user's explicit declaration **« le travail est terminé »** confirms their
review of the current branch and authorizes merging into the main branch, then
deleting the local and remote work branch after a successful merge. Quoting the
phrase in a question or instruction is not authorization. Green CI alone is not
user validation. Before an authorized merge, check current results, resolve
conflicts and report actual blockers.

## Documentation and communication

Write for developers, including juniors. Lead with the technical action or
result, use concrete commands and examples, and explain unfamiliar terms briefly.
Remove repetition, conversational history and filler. Keep constraints and
validation limits explicit.

On first template use, document the project's objective, technologies, targets,
layout and validation. Do not invent a license or repository visibility. Do not
present generic checks as product builds or tests. Apply recorded preferences
without asking the user to repeat them. Clearly distinguish proposed changes,
implemented changes, validated results and remaining checks.
