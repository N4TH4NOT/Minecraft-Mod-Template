#!/usr/bin/env python3
"""Check the reusable scaffold; Java sources are optional in a template."""

import argparse
import json
from pathlib import Path
import re
import tomllib
import zipfile

from plan import discover


def properties(path):
    result = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith(("#", "!")):
            key, separator, value = line.partition("=")
            if separator:
                result[key.strip()] = value.strip()
    return result


def require(path):
    if not path.is_file():
        raise ValueError(f"Missing scaffold file: {path}")


def validate_wrapper(directory):
    for name in ("gradlew", "gradlew.bat", "gradle/wrapper/gradle-wrapper.properties", "gradle/wrapper/gradle-wrapper.jar"):
        require(directory / name)
    config = properties(directory / "gradle/wrapper/gradle-wrapper.properties")
    url = config.get("distributionUrl", "").replace("\\:", ":")
    distribution = re.fullmatch(r"https://services\.gradle\.org/distributions/gradle-(\d+(?:\.\d+)+)-(?:bin|all)\.zip", url)
    if not distribution:
        raise ValueError(f"Invalid Gradle distribution URL in {directory}")
    if not re.fullmatch(r"[a-fA-F0-9]{64}", config.get("distributionSha256Sum", "")):
        raise ValueError(f"A SHA-256 distribution checksum is required in {directory}")
    with zipfile.ZipFile(directory / "gradle/wrapper/gradle-wrapper.jar") as archive:
        if "org/gradle/wrapper/GradleWrapperMain.class" not in archive.namelist():
            raise ValueError(f"Gradle wrapper main class is absent in {directory}")
    return tuple(int(part) for part in distribution.group(1).split("."))


def expand(text, config, json_resource=False):
    def replace(match):
        key = match.group(1)
        if key not in config:
            raise ValueError(f"Resource references undefined property {key!r}")
        value = config[key]
        # JSON metadata places numbers outside strings and text inside strings.
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
        # A template can retain service declarations before any Java code exists.


def validate(root):
    for name in ("settings.gradle", "build.gradle", "gradle.properties", "README.md", "AGENTS.md"):
        require(root / name)
    config = properties(root / "gradle.properties")
    for key in ("version", "group", "mod_id", "minecraft_version", "java_version"):
        if not config.get(key):
            raise ValueError(f"Required project property {key!r} is empty or absent")
    if not config["java_version"].isdigit():
        raise ValueError("java_version must be a Java language version number")
    root_gradle_version = validate_wrapper(root)
    modules, minestom = discover(root)
    if any(module in ("fabric", "forge", "neoforge") for module in modules):
        if config["java_version"] != "21" or root_gradle_version[0] != 8:
            raise ValueError("Modloader targets require java_version=21 and the Gradle 8 wrapper")
    descriptors = {
        "common": "pack.mcmeta",
        "fabric": "fabric.mod.json",
        "forge": "META-INF/mods.toml",
        "neoforge": "META-INF/neoforge.mods.toml",
    }
    for module in modules:
        directory = root / module
        if module in descriptors:
            validate_resource(directory / "src/main/resources" / descriptors[module], config)
        for resource in (directory / "src/main/resources").glob("*.mixins.json"):
            validate_resource(resource, config)
        validate_services(directory)
    if minestom:
        minestom_gradle_version = validate_wrapper(root / "minestom")
        minestom_config = dict(config)
        extra = root / "minestom/gradle.properties"
        if extra.is_file():
            minestom_config.update(properties(extra))
        version = minestom_config.get("minestom_version", "")
        if not version.endswith("-" + config["minecraft_version"]):
            raise ValueError("minestom_version must explicitly target minecraft_version")
        if minestom_config.get("minestom_java_version") != "25":
            raise ValueError("The configured Minestom target requires minestom_java_version=25")
        if minestom_gradle_version < (9, 1):
            raise ValueError("Java 25 Minestom requires a standalone Gradle 9.1 or newer wrapper")
        validate_services(root / "minestom")
    if not any(module in descriptors and module != "common" for module in modules) and not minestom:
        raise ValueError("No supported application target remains in the template")
    return {"result": "passed", "mode": "template", "modules": modules,
            "minestom": minestom, "java_sources_required": False,
            "checks": ["project properties", "module declarations", "wrapper files and checksum declarations",
                       "resource placeholders and syntax", "service declarations"],
            "application_builds_executed": False}


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
