#!/usr/bin/env python3
"""Select template checks or application builds without executing Gradle."""

import argparse
import json
from pathlib import Path
import re


MOD_LOADERS = ("fabric", "forge", "neoforge")
TEST_LANGUAGES = ("java", "groovy", "kotlin")


def configured_modules(manifest):
    if not manifest.is_file():
        raise ValueError("Missing shared module manifest: gradle/modules.txt.")
    modules = []
    for line in manifest.read_text(encoding="utf-8").splitlines():
        module = line.partition("#")[0].strip()
        if not module:
            continue
        if not re.fullmatch(r"[A-Za-z0-9_-]+(?:/[A-Za-z0-9_-]+)*", module):
            raise ValueError(f"Invalid module path {module!r} in gradle/modules.txt.")
        if module == "minestom":
            raise ValueError("Minestom is a standalone build; do not add it to gradle/modules.txt.")
        if module in modules:
            raise ValueError(f"Duplicate module {module!r} in gradle/modules.txt.")
        modules.append(module)
    return modules


def has_sources(directory, source_set="main"):
    extensions = ("java",) if source_set == "main" else TEST_LANGUAGES
    return any(
        next((directory / "src" / source_set).rglob("*." + extension), None) is not None
        for extension in extensions
    )


def discover(root):
    settings = root / "settings.gradle"
    if not settings.is_file():
        raise ValueError("Missing root settings.gradle.")
    modules = []
    for module in configured_modules(root / "gradle/modules.txt"):
        directory = root / module
        if not directory.exists() and not directory.is_symlink():
            continue
        if not directory.is_dir() or not (directory / "build.gradle").is_file():
            raise ValueError(f"Module {module!r} is present but has no build.gradle.")
        modules.append(module)
    if "common" not in modules:
        raise ValueError("The common module is required: retain common/build.gradle and its gradle/modules.txt entry.")
    minestom = root / "minestom"
    minestom_present = minestom.exists() or minestom.is_symlink()
    standalone_files = [(minestom / name).is_file() for name in ("settings.gradle", "build.gradle")]
    if minestom_present and (not minestom.is_dir() or not all(standalone_files)):
        raise ValueError("Minestom requires both minestom/settings.gradle and minestom/build.gradle.")
    return modules, minestom_present


def repository_type(requested, metadata):
    if requested in ("template", "project"):
        return requested
    if not isinstance(metadata, bool):
        raise ValueError("repository.is_template is unavailable; use the repository_type override.")
    return "template" if metadata else "project"


def make_plan(root, kind):
    modules, minestom = discover(root)
    declared = configured_modules(root / "gradle/modules.txt") + ["minestom"]
    included = modules + (["minestom"] if minestom else [])
    loaders = [name for name in MOD_LOADERS if name in modules]
    if not loaders and not minestom:
        raise ValueError("No configured application target: retain a modloader module or standalone Minestom.")
    matrix = []
    if kind == "project":
        application_modules = [root / name for name in modules]
        if minestom:
            application_modules.append(root / "minestom")
        if not any(has_sources(directory) for directory in application_modules):
            raise ValueError("Derived project has no Java application sources. No application build can be validated.")
        matrix.extend({"target": name, "kind": "mod", "java": "21", "common": "common" in modules}
                      for name in loaders)
        if minestom:
            matrix.append({"target": "minestom", "kind": "minestom", "java": "25", "common": False})
    return {
        "repository_type": kind,
        "matrix": {"include": matrix},
        "has_builds": bool(matrix),
        "support_tests": kind == "project" and bool(loaders) and has_sources(root / "buildSrc", "test"),
        "declared_modules": declared,
        "included_modules": included,
        "excluded_modules": [module for module in declared if module not in included],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--repository-type", choices=("auto", "template", "project"), default="auto")
    parser.add_argument("--repository-is-template", choices=("true", "false"))
    parser.add_argument("--event-path", type=Path)
    parser.add_argument("--github-output", type=Path)
    args = parser.parse_args()
    try:
        metadata = None
        if args.event_path:
            metadata = json.loads(args.event_path.read_text()).get("repository", {}).get("is_template")
        if args.repository_is_template is not None:
            metadata = args.repository_is_template == "true"
        kind = repository_type(args.repository_type, metadata)
        plan = make_plan(args.root, kind)
        print(json.dumps(plan, indent=2))
        if args.github_output:
            with args.github_output.open("a", encoding="utf-8") as output:
                for key, value in plan.items():
                    encoded = value if isinstance(value, str) else json.dumps(value, separators=(",", ":"))
                    output.write(f"{key}={encoded}\n")
    except (ValueError, OSError) as error:
        parser.exit(1, f"CI plan failed: {error}\n")


if __name__ == "__main__":
    main()
