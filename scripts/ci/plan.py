#!/usr/bin/env python3
"""Select template checks or project builds from the central Gradle properties."""

import argparse
import json
from pathlib import Path
import re


MOD_LOADERS = ("fabric", "forge", "neoforge")
TEST_LANGUAGES = ("java", "groovy", "kotlin")


def properties(path):
    result = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith(("#", "!")):
            key, separator, value = line.partition("=")
            if separator:
                result[key.strip()] = value.strip()
    return result


def module_list(config, key, allow_empty=False):
    if key not in config:
        raise ValueError(f"Missing central property {key!r} in gradle.properties.")
    modules = [item.strip() for item in config[key].split(",") if item.strip()]
    if not modules and not allow_empty:
        raise ValueError(f"Central property {key!r} must contain at least one module.")
    for module in modules:
        if not re.fullmatch(r"[A-Za-z0-9_-]+(?:/[A-Za-z0-9_-]+)*", module):
            raise ValueError(f"Invalid module path {module!r} in {key}.")
    if len(modules) != len(set(modules)):
        raise ValueError(f"Duplicate module in central property {key!r}.")
    return modules


def configured_modules(configuration):
    return module_list(properties(configuration), "modules")


def empty_module(directory):
    return directory.is_dir() and not any(path.name != ".gitkeep" for path in directory.iterdir())


def central_build(root, module):
    return root / "gradle/modules" / (module + ".gradle")


def discover(root):
    if not (root / "settings.gradle").is_file():
        raise ValueError("Missing root settings.gradle.")
    config = properties(root / "gradle.properties")
    declared = module_list(config, "modules")
    required = module_list(config, "required_modules")
    standalone = module_list(config, "standalone_modules", allow_empty=True)
    if "common" not in declared or "common" not in required or "common" in standalone:
        raise ValueError("The common module is required in modules and required_modules and must use the root build.")
    if not set(required + standalone).issubset(declared):
        raise ValueError("required_modules and standalone_modules must be subsets of modules.")
    if "minestom" in declared and "minestom" not in standalone:
        raise ValueError("Minestom is a standalone build; add it to standalone_modules.")
    modules = []
    present = []
    for module in declared:
        directory = root / module
        if not directory.exists() and not directory.is_symlink():
            continue
        if not directory.is_dir():
            raise ValueError(f"Module {module!r} exists but is not a directory.")
        preset = root / "gradle/templates" / module
        if empty_module(directory):
            if not central_build(root, module).is_file() or not preset.is_dir() or not any(preset.iterdir()):
                raise ValueError(f"Empty module {module!r} needs its central build and initialization preset.")
        elif module in standalone:
            if not (directory / "settings.gradle").is_file() or not central_build(root, module).is_file():
                raise ValueError(f"Standalone module {module!r} needs settings.gradle and its central build configuration.")
        elif not (directory / "build.gradle").is_file() and not central_build(root, module).is_file():
            raise ValueError(f"Module {module!r} is present but has neither build.gradle nor a central build configuration.")
        present.append(module)
        if module not in standalone:
            modules.append(module)
    for module in required:
        if module not in present:
            raise ValueError(f"The {module} module is required: retain its directory and central configuration.")
    return modules, "minestom" in present


def has_sources(directory, source_set="main"):
    extensions = ("java",) if source_set == "main" else TEST_LANGUAGES
    return any(next((directory / "src" / source_set).rglob("*." + extension), None) is not None
               for extension in extensions)


def language_version(config, key, fallback=None):
    value = config.get(key, fallback)
    if value is None or not re.fullmatch(r"[1-9][0-9]*", str(value)):
        raise ValueError(f"{key} must be a positive Java language version number.")
    return str(value)


def module_java(config, module):
    return language_version(config, module.replace("/", "_") + "_java_version", config.get("java_version"))


def java_setup(config, targets, standalone=False, bootstrap=False):
    runtime_key = targets[0] + "_gradle_java_version" if standalone else "gradle_java_version"
    runtime = language_version(config, runtime_key)
    toolchains = {module_java(config, module) for module in targets}
    if not standalone:
        toolchains.add(module_java(config, "buildsrc"))
    if bootstrap:
        toolchains.add(language_version(config, "gradle_java_version"))
    versions = sorted(toolchains - {runtime}, key=int) + [runtime]
    return runtime, "\n".join(versions)


def repository_type(requested, metadata):
    if requested in ("template", "project"):
        return requested
    if not isinstance(metadata, bool):
        raise ValueError("repository.is_template is unavailable; use the repository_type override.")
    return "template" if metadata else "project"


def make_plan(root, kind):
    config = properties(root / "gradle.properties")
    declared = module_list(config, "modules")
    standalone = module_list(config, "standalone_modules", allow_empty=True)
    modules, minestom = discover(root)
    included = [module for module in declared if (root / module).is_dir()]
    initializing = [module for module in included if empty_module(root / module)]
    loaders = [name for name in MOD_LOADERS if name in modules]
    if not loaders and not minestom:
        raise ValueError("No configured application target: retain a modloader module or standalone Minestom.")
    matrix = []
    scaffold_runtime, scaffold_versions = java_setup(config, ["common", "buildsrc"])
    scaffold_toolchains = set(scaffold_versions.split())
    if minestom:
        scaffold_toolchains.update(java_setup(config, ["minestom"], standalone=True)[1].split())
    scaffold_versions = "\n".join(sorted(scaffold_toolchains - {scaffold_runtime}, key=int) + [scaffold_runtime])
    if kind == "project":
        application_directories = [root / module for module in included]
        application_directories += [root / "gradle/templates" / module for module in initializing]
        if not any(has_sources(directory) for directory in application_directories):
            raise ValueError("Derived project has no Java application sources or initialization sources. No application build can be validated.")
        for target in loaders + (["minestom"] if minestom else []):
            is_standalone = target in standalone
            targets = [target] if is_standalone else [target, "common"]
            runtime, versions = java_setup(config, targets, is_standalone, bool(initializing))
            matrix.append({"target": target, "kind": "minestom" if is_standalone else "mod",
                           "java": runtime, "java_versions": versions, "common": not is_standalone,
                           "initialize": bool(initializing),
                           "bootstrap_java": language_version(config, "gradle_java_version")})
    return {
        "repository_type": kind, "matrix": {"include": matrix}, "has_builds": bool(matrix),
        "support_tests": kind == "project" and bool(loaders) and has_sources(root / "buildSrc", "test"),
        "gradle_java_version": language_version(config, "gradle_java_version"),
        "support_java_versions": java_setup(config, ["buildsrc"])[1],
        "scaffold_java_versions": scaffold_versions,
        "declared_modules": declared, "included_modules": included,
        "excluded_modules": [module for module in declared if module not in included],
        "initialization_modules": initializing,
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
        plan = make_plan(args.root, repository_type(args.repository_type, metadata))
        print(json.dumps(plan, indent=2))
        if args.github_output:
            with args.github_output.open("a", encoding="utf-8") as output:
                for key, value in plan.items():
                    encoded = value if isinstance(value, str) else json.dumps(value, separators=(",", ":"))
                    if "\n" in encoded:
                        delimiter = "CI_OUTPUT_" + key.upper()
                        output.write(f"{key}<<{delimiter}\n{encoded}\n{delimiter}\n")
                    else:
                        output.write(f"{key}={encoded}\n")
    except (ValueError, OSError) as error:
        parser.exit(1, f"CI plan failed: {error}\n")


if __name__ == "__main__":
    main()
