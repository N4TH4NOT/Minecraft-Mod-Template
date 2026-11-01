#!/usr/bin/env python3
"""Select template checks or application builds without executing Gradle."""

import argparse
import json
from pathlib import Path
import re


MOD_LOADERS = ("fabric", "forge", "neoforge")
TEST_LANGUAGES = ("java", "groovy", "kotlin")


def included_modules(settings):
    text = settings.read_text(encoding="utf-8")
    # Keep quoted URLs and strings intact while removing both inline and block comments.
    text = re.sub(r'''("(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*')|/\*.*?\*/|//[^\n]*''',
                  lambda match: match.group(1) or "", text, flags=re.S)
    declarations = re.findall(r"(?m)^\s*include\b\s*(?:\((.*?)\)|([^\n]+))", text, re.S)
    modules = set()
    for parenthesized, inline in declarations:
        for name in re.findall(r"['\"](:?[\w:-]+)['\"]", parenthesized or inline):
            modules.add(name.lstrip(":").replace(":", "/"))
    return sorted(modules)


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
    modules = included_modules(settings)
    if "minestom" in modules:
        raise ValueError("Minestom is a standalone build; do not include it in root settings.gradle.")
    for module in modules:
        if not (root / module / "build.gradle").is_file():
            raise ValueError(f"Module {module!r} is declared but has no build.gradle.")
    minestom = root / "minestom"
    standalone_files = [(minestom / name).is_file() for name in ("settings.gradle", "build.gradle")]
    if any(standalone_files) and not all(standalone_files):
        raise ValueError("Minestom requires both minestom/settings.gradle and minestom/build.gradle.")
    return modules, all(standalone_files)


def repository_type(requested, metadata):
    if requested in ("template", "project"):
        return requested
    if not isinstance(metadata, bool):
        raise ValueError("repository.is_template is unavailable; use the repository_type override.")
    return "template" if metadata else "project"


def make_plan(root, kind):
    modules, minestom = discover(root)
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
