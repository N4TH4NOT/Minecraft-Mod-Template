#!/usr/bin/env python3
"""Check reusable configuration; source code may be absent or initialized later."""

import argparse
import json
from pathlib import Path
import re
import tomllib
import zipfile

from plan import discover, empty_module, language_version, module_java, properties


def require(path):
    if not path.is_file():
        raise ValueError(f"Missing scaffold file: {path}")


def version(value, key):
    if not re.fullmatch(r"[1-9][0-9]*\.[0-9]+(?:\.[0-9]+)?", value or ""):
        raise ValueError(f"{key} must be a stable Gradle version number.")
    return tuple(int(part) for part in value.split("."))


def validate_wrapper(directory, config, prefix="", preset=False):
    for name in ("gradlew", "gradlew.bat", "gradle/wrapper/gradle-wrapper.properties", "gradle/wrapper/gradle-wrapper.jar"):
        require(directory / name)
    wrapper = properties(directory / "gradle/wrapper/gradle-wrapper.properties")
    if preset:
        tokens = {"__MIN_GRADLE_VERSION__": config.get("minestom_gradle_version", ""),
                  "__MIN_GRADLE_SHA256__": config.get("minestom_gradle_distribution_sha256", "")}
        for key, value in wrapper.items():
            for token, replacement in tokens.items():
                value = value.replace(token, replacement)
            wrapper[key] = value
    expected_version = config.get(prefix + "gradle_version", "")
    expected_checksum = config.get(prefix + "gradle_distribution_sha256", "")
    declared_version = version(expected_version, prefix + "gradle_version")
    expected_url = f"https://services.gradle.org/distributions/gradle-{expected_version}-bin.zip"
    if wrapper.get("distributionUrl", "").replace("\\:", ":") != expected_url:
        raise ValueError(f"Wrapper distribution in {directory} differs from central {prefix}gradle_version.")
    if not re.fullmatch(r"[a-fA-F0-9]{64}", expected_checksum):
        raise ValueError(f"Central {prefix}gradle_distribution_sha256 must be a SHA-256 checksum.")
    if wrapper.get("distributionSha256Sum", "").lower() != expected_checksum.lower():
        raise ValueError(f"Wrapper SHA-256 in {directory} differs from central {prefix}gradle_distribution_sha256.")
    with zipfile.ZipFile(directory / "gradle/wrapper/gradle-wrapper.jar") as archive:
        if "org/gradle/wrapper/GradleWrapperMain.class" not in archive.namelist():
            raise ValueError(f"Gradle wrapper main class is absent in {directory}")
    return declared_version


def validate_java(gradle, java, runtime=False):
    # Official Gradle Java compatibility: runtime and toolchain minimums differ.
    runtime_minimums = {8: (2, 0), 9: (4, 3), 10: (4, 7), 11: (5, 0), 12: (5, 4),
                        13: (6, 0), 14: (6, 3), 15: (6, 7), 16: (7, 0), 17: (7, 3),
                        18: (7, 5), 19: (7, 6), 20: (8, 3), 21: (8, 5), 22: (8, 8),
                        23: (8, 10), 24: (8, 14), 25: (9, 1)}
    minimums = dict(runtime_minimums)
    if not runtime:
        minimums.update({20: (8, 1), 21: (8, 4), 22: (8, 7)})
    java = int(java)
    if java not in minimums:
        raise ValueError(f"Java {java} has no known Gradle compatibility rule in this template; update the compatibility table.")
    if gradle < minimums[java]:
        raise ValueError(f"Java {java} {'runtime' if runtime else 'toolchain'} requires Gradle {'.'.join(map(str, minimums[java]))} or newer.")
    if runtime and gradle[0] >= 9 and java < 17:
        raise ValueError("Gradle 9 requires a Java runtime of at least 17.")


def expand(text, config, json_resource=False):
    def replace(match):
        key = match.group(1)
        if key not in config:
            raise ValueError(f"Resource references undefined property {key!r}")
        value = config[key]
        return json.dumps(value, ensure_ascii=False)[1:-1] if json_resource else value
    return re.sub(r"\$\{([A-Za-z_]\w*)\}", replace, text)


def validate_resource(path, config):
    require(path)
    text = path.read_text(encoding="utf-8")
    if path.suffix in (".json", ".mcmeta"):
        json.loads(expand(text, config, json_resource=True))
    else:
        tomllib.loads(expand(text, config))


def validate_services(directory):
    qualified_name = r"[A-Za-z_$][\w$]*(?:\.[A-Za-z_$][\w$]*)+"
    for service in sorted((directory / "src/main/resources/META-INF/services").glob("*")):
        if not service.is_file():
            continue
        if not re.fullmatch(qualified_name, service.name):
            raise ValueError(f"Invalid service interface name: {service}")
        providers = [line.partition("#")[0].strip() for line in service.read_text().splitlines()]
        providers = [name for name in providers if name]
        if not providers or any(not re.fullmatch(qualified_name, name) for name in providers):
            raise ValueError(f"Missing or invalid service provider: {service}")


def validate(root):
    for name in ("settings.gradle", "build.gradle", "gradle.properties", "gradle/build-plan.gradle",
                 "gradle/scaffold.gradle", "gradle/bootstrap/settings.gradle", "gradle/bootstrap/build.gradle",
                 "README.md", "AGENTS.md"):
        require(root / name)
    config = properties(root / "gradle.properties")
    for key in ("version", "group", "mod_id", "minecraft_version", "java_version"):
        if not config.get(key):
            raise ValueError(f"Required project property {key!r} is empty or absent")
    language_version(config, "java_version")
    modules, minestom = discover(root)
    root_gradle = validate_wrapper(root, config)
    root_runtime = language_version(config, "gradle_java_version")
    validate_java(root_gradle, root_runtime, runtime=True)
    buildsrc_java = module_java(config, "buildsrc")
    validate_java(root_gradle, buildsrc_java)
    if int(buildsrc_java) > int(root_runtime):
        raise ValueError("buildsrc_java_version cannot exceed gradle_java_version: Gradle must load the buildSrc bytecode.")
    if "forge" in modules and config.get("forgegradle_version", "").split(".")[0] == "6" and root_gradle[0] >= 9:
        raise ValueError("ForgeGradle 6 requires a root Gradle version below 9.")
    descriptors = {"common": "pack.mcmeta", "fabric": "fabric.mod.json",
                   "forge": "META-INF/mods.toml", "neoforge": "META-INF/neoforge.mods.toml"}
    initializing = []
    for module in modules:
        directory = root / module
        java = module_java(config, module)
        validate_java(root_gradle, java)
        if config["minecraft_version"] == "1.21.10" and module in descriptors and int(java) < 21:
            raise ValueError(f"Minecraft 1.21.10 requires a Java toolchain of at least 21 for {module}.")
        if empty_module(directory):
            initializing.append(module)
            continue
        resource_config = dict(config, java_version=java)
        if module in descriptors:
            validate_resource(directory / "src/main/resources" / descriptors[module], resource_config)
        for resource in (directory / "src/main/resources").glob("*.mixins.json"):
            validate_resource(resource, resource_config)
        validate_services(directory)
    if minestom:
        directory = root / "minestom"
        wrapper_root = root / "gradle/templates/minestom" if empty_module(directory) else directory
        require(wrapper_root / "settings.gradle")
        minestom_gradle = validate_wrapper(wrapper_root, config, "minestom_", preset=empty_module(directory))
        validate_java(minestom_gradle, language_version(config, "minestom_gradle_java_version"), runtime=True)
        minestom_java = module_java(config, "minestom")
        validate_java(minestom_gradle, minestom_java)
        if config["minecraft_version"] == "1.21.10" and int(minestom_java) < 25:
            raise ValueError("The configured Minestom 1.21.10 release requires a Java toolchain of at least 25.")
        if not config.get("minestom_version", "").endswith("-" + config["minecraft_version"]):
            raise ValueError("minestom_version must explicitly target minecraft_version")
        if empty_module(directory):
            initializing.append("minestom")
        else:
            validate_services(directory)
    if not any(module in descriptors and module != "common" for module in modules) and not minestom:
        raise ValueError("No supported application target remains in the template")
    return {"result": "passed", "mode": "template", "modules": modules, "minestom": minestom,
            "initialization_modules": initializing, "java_sources_required": False,
            "checks": ["central project and module properties", "present directories and initialization presets",
                       "wrapper version and checksum consistency", "Java and Gradle compatibility",
                       "resource placeholders and syntax", "service declarations"], "application_builds_executed": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    try:
        report = validate(args.root)
    except (ValueError, OSError, zipfile.BadZipFile) as error:
        report = {"result": "failed", "mode": "template", "error": str(error)}
    text = json.dumps(report, indent=2)
    print(text)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(text + "\n", encoding="utf-8")
    if report["result"] != "passed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
