**English** | [Français](versionnement.fr.md)

# Versioning

The `version` property in `gradle.properties` defines the product version for
all modules, independently of Minecraft and dependency versions.

| Delivered change | Semantic Versioning 2.0.0 | Example |
| --- | --- | --- |
| Compatible fix | PATCH | `1.4.2` → `1.4.3` |
| Compatible feature | MINOR, reset PATCH | `1.4.2` → `1.5.0` |
| Breaking public contract change | MAJOR, reset MINOR and PATCH | `1.4.2` → `2.0.0` |

Assess the branch since the last normal release, without counting commits.
Documentation, tests and CI do not automatically require a version change.
`0.y.z` remains unstable; there is no automatic move to `1.0.0`.

A work branch may use a prerelease. On `main`, keep exactly `MAJOR.MINOR.PATCH`:
three integers with no leading zeros except `0`, and no prefix, prerelease suffix
or build metadata.

Before an authorized merge:

1. Set the normal version on the work branch.
2. Obtain successful CI results for that exact commit.
3. Merge the tested commit without changing its version afterward on `main`.

Never reuse the version number of a distributed artifact for different content.
See [CI validation](validation.md).
