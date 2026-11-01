#!/usr/bin/env python3
"""Confirm configured versions in publisher metadata without fetching dependencies."""

import argparse
from collections import Counter
from dataclasses import dataclass
from http.client import HTTPException
import json
from pathlib import Path
import re
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

from plan import module_list, properties


CENTRAL = "https://repo.maven.apache.org/maven2/"
FABRIC = "https://maven.fabricmc.net/"
FORGE = "https://maven.minecraftforge.net/"
NEO = "https://maven.neoforged.net/releases/"
SPONGE = "https://repo.spongepowered.org/repository/maven-public/"
PORTAL = "https://plugins.gradle.org/m2/"
MOJANG = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"
MAX_METADATA = 4 * 1024 * 1024
SEMVER = re.compile(r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
                    r"(?:-((?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*)(?:\.(?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*))*))?"
                    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?")


@dataclass
class Response:
    status: int
    body: bytes = b""
    content_type: str = ""


class VerificationError(Exception):
    def __init__(self, message, status="failed"):
        super().__init__(message)
        self.status = status


class HttpReader:
    """GET bounded metadata only; the catalog contains no binary artifact URLs."""
    def __init__(self, timeout=12):
        self.timeout = timeout

    def __call__(self, url):
        request = urllib.request.Request(url, headers={
            "User-Agent": "MinecraftTemplatePublicationCheck/1.0", "Accept-Encoding": "identity"})
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as result:
                return Response(result.status, result.read(MAX_METADATA + 1), result.headers.get_content_type())
        except urllib.error.HTTPError as error:
            return Response(error.code, content_type=error.headers.get_content_type() if error.headers else "")


class Remote:
    def __init__(self, reader=None, attempts=3, ttl=180, clock=time.monotonic, pause=time.sleep):
        self.reader = reader or HttpReader()
        self.attempts = attempts
        self.ttl = ttl
        self.clock = clock
        self.pause = pause
        self.cache = {}

    def get(self, url):
        if not url.startswith("https://"):
            raise VerificationError(f"Metadata URL must use HTTPS: {url}")
        cached = self.cache.get(url)
        if cached and self.clock() - cached[0] < self.ttl:
            response = cached[1]
        else:
            response = None
            for attempt in range(self.attempts):
                try:
                    response = self.reader(url)
                except (urllib.error.URLError, TimeoutError, OSError, HTTPException) as error:
                    reason = error.reason if isinstance(error, urllib.error.URLError) else error
                    tls = isinstance(reason, ssl.SSLError)
                    if not tls and attempt + 1 < self.attempts:
                        self.pause(0.25 * (attempt + 1))
                        continue
                    label = "TLS error" if tls else "network error"
                    raise VerificationError(f"Unverified publisher ({label}): {url}: {reason}", "unverified") from error
                if response.status == 429 or 500 <= response.status < 600:
                    if attempt + 1 < self.attempts:
                        self.pause(0.25 * (attempt + 1))
                        continue
                break
            if response is None:
                raise VerificationError(f"Publisher returned no response: {url}", "unverified")
            if response.status in (200, 404, 410):
                self.cache[url] = self.clock(), response
        if response.status in (404, 410):
            raise VerificationError(f"Publication metadata not found (HTTP {response.status}): {url}")
        if response.status != 200:
            raise VerificationError(f"Unverified publisher response HTTP {response.status}: {url}", "unverified")
        if len(response.body) > MAX_METADATA:
            raise VerificationError(f"Publisher metadata exceeds the size limit: {url}", "unverified")
        if "html" in response.content_type.lower():
            raise VerificationError(f"Publisher returned HTML instead of metadata: {url}")
        return response.body


def fixed_version(value):
    if not value or "snapshot" in value.lower() or not re.fullmatch(r"[0-9][A-Za-z0-9]*(?:[._+\-][A-Za-z0-9]+)*", value):
        raise VerificationError("Expected a fixed version; dynamic selectors, ranges and mutable SNAPSHOTs are not publication pins.")


def text(element, path):
    return (element.findtext(path) or "").strip()


def maven_url(repository, group, artifact, value):
    quoted = urllib.parse.quote(value, safe="")
    return f"{repository}{group.replace('.', '/')}/{artifact}/{quoted}/{artifact}-{quoted}.pom"


def published_pom(remote, sources, repository, group, artifact, value):
    fixed_version(value)
    url = maven_url(repository, group, artifact, value)
    sources.append(url)
    try:
        document = ET.fromstring(remote.get(url))
    except ET.ParseError as error:
        raise VerificationError(f"Invalid publisher XML: {url}") from error
    if document.tag.rsplit("}", 1)[-1] != "project":
        raise VerificationError(f"Publisher XML is not a Maven POM: {url}")
    actual_group = text(document, "{*}groupId") or text(document, "{*}parent/{*}groupId")
    actual_version = text(document, "{*}version") or text(document, "{*}parent/{*}version")
    actual_artifact = text(document, "{*}artifactId")
    if (actual_group, actual_artifact, actual_version) != (group, artifact, value):
        raise VerificationError(f"POM identity does not match {group}:{artifact}:{value}: {url}")


def published_minecraft(config, key, remote, sources):
    fixed_version(config[key])
    sources.append(MOJANG)
    try:
        manifest = json.loads(remote.get(MOJANG))
    except (ValueError, UnicodeError) as error:
        raise VerificationError("Invalid official Minecraft version manifest JSON.") from error
    if not isinstance(manifest, dict) or not isinstance(manifest.get("versions"), list):
        raise VerificationError("Invalid official Minecraft version manifest structure.")
    if not any(isinstance(item, dict) and item.get("id") == config[key] for item in manifest["versions"]):
        raise VerificationError(f"Minecraft {config[key]} is absent from the official version manifest.")
    return "The official Minecraft manifest lists this version."


def published_gradle(config, prefix, remote, sources):
    value = config[prefix + "gradle_version"]
    fixed_version(value)
    url = f"https://services.gradle.org/distributions/gradle-{value}-bin.zip.sha256"
    sources.append(url)
    try:
        checksum = remote.get(url).decode("ascii").strip().lower()
    except UnicodeError as error:
        raise VerificationError("Official Gradle checksum metadata is not ASCII.") from error
    if not re.fullmatch(r"[a-f0-9]{64}", checksum):
        raise VerificationError("Official Gradle checksum metadata is malformed.")
    if checksum != config[prefix + "gradle_distribution_sha256"].lower():
        raise VerificationError("Configured distribution SHA-256 differs from official Gradle metadata.")
    return "Official checksum metadata confirms this Gradle distribution; no archive was fetched."


# Plugin marker POMs confirm the configured plugin release. No marker JAR is requested.
PLUGIN_PINS = {
    "fabric_loom_version": (FABRIC, "fabric-loom", {"fabric"}),
    "moddevgradle_version": (PORTAL, "net.neoforged.moddev", {"common", "neoforge"}),
    "forgegradle_version": (FORGE, "net.minecraftforge.gradle", {"forge"}),
    "mixingradle_version": (SPONGE, "org.spongepowered.mixin", {"forge"}),
    "foojay_resolver_version": (PORTAL, "org.gradle.toolchains.foojay-resolver-convention", {"root"}),
}
MAVEN_PINS = {
    "fabric_loader_version": (FABRIC, "net.fabricmc", "fabric-loader", {"fabric"}),
    "fabric_version": (FABRIC, "net.fabricmc.fabric-api", "fabric-api", {"fabric"}),
    "cloth_config_version": ("https://maven.shedaniel.me/", "me.shedaniel.cloth", "cloth-config-fabric", {"fabric"}),
    "modmenu_version": ("https://maven.terraformersmc.com/releases/", "com.terraformersmc", "modmenu", {"fabric"}),
    "forge_version": (FORGE, "net.minecraftforge", "forge", {"forge"}),
    "neoforge_version": (NEO, "net.neoforged", "neoforge", {"neoforge"}),
    "neo_form_version": (NEO, "net.neoforged", "neoform", {"common"}),
    "parchment_version": (NEO, "org.parchmentmc.data", "parchment-", {"common", "fabric", "neoforge"}),
    "minestom_version": (CENTRAL, "net.minestom", "minestom", {"minestom"}),
    "mixin_version": (SPONGE, "org.spongepowered", "mixin", {"common", "forge"}),
    "mixinextras_version": (CENTRAL, "io.github.llamalad7", "mixinextras-", {"common", "fabric", "forge", "neoforge"}),
    "junit_version": (CENTRAL, "org.junit", "junit-bom", {"common", "fabric", "forge", "neoforge", "minestom", "buildsrc"}),
    "gson_version": (CENTRAL, "com.google.code.gson", "gson", {"common", "fabric", "forge", "neoforge"}),
    "tomlj_version": (CENTRAL, "org.tomlj", "tomlj", {"forge", "neoforge"}),
    "slf4j_version": (CENTRAL, "org.slf4j", "slf4j-api", {"common", "minestom"}),
    "jopt_simple_version": (CENTRAL, "net.sf.jopt-simple", "jopt-simple", {"forge"}),
}
PARAMETERS = {"minecraft_data_version", "minecraft_pack_version", "minecraft_version_range",
              "forge_loader_version_range", "neoforge_loader_version_range"}
DISTRIBUTIONS = {"gradle_version", "gradle_distribution_sha256", "minestom_gradle_version", "minestom_gradle_distribution_sha256"}
MODULE_SCOPES = {"common", "fabric", "forge", "neoforge", "minestom"}
PARAMETER_SCOPES = {
    "minecraft_data_version": MODULE_SCOPES - {"minestom"},
    "minecraft_pack_version": MODULE_SCOPES - {"minestom"},
    "minecraft_version_range": {"forge", "neoforge"},
    "forge_loader_version_range": {"forge"},
    "neoforge_loader_version_range": {"neoforge"},
}
SCOPE_LABELS = {"common": "Common", "fabric": "Fabric", "forge": "Forge", "neoforge": "NeoForge",
                "minestom": "Minestom", "buildsrc": "buildSrc", "root": "Root build",
                "configuration": "Project configuration"}


def presentation_scope(key, config, active):
    """Describe consumers without changing publication checks or their scopes."""
    group = None
    if key in PLUGIN_PINS:
        scope = set(PLUGIN_PINS[key][2])
    elif key in MAVEN_PINS:
        scope = set(MAVEN_PINS[key][3])
    elif key == "minecraft_version":
        scope = set(MODULE_SCOPES)
    elif key == "parchment_minecraft":
        scope = set(MAVEN_PINS["parchment_version"][3])
    elif key in DISTRIBUTIONS or key.endswith("java_version") and key != "java_version":
        group = "Build tooling"
        owner = key.removesuffix("_gradle_java_version").removesuffix("_java_version")
        scope = {"minestom" if key.startswith("minestom_") else "root" if key in DISTRIBUTIONS or key == "gradle_java_version" else owner}
    elif key == "java_version":
        group, scope = "Configuration", (MODULE_SCOPES - {"minestom"}) | {"buildsrc"}
    else:
        group, scope = "Configuration", set(PARAMETER_SCOPES.get(key, {"configuration"}))
    used = scope & (set(active) | {"configuration"})
    if key == "java_version":
        used = {owner for owner in used if not config.get(owner + "_java_version")}
    consumers = used or scope
    if group is None:
        if consumers <= {"root", "buildsrc"}:
            group = "Build tooling"
        elif len(consumers) == 1:
            group = SCOPE_LABELS[next(iter(consumers))]
        else:
            group = "Shared dependencies"
    return {"scope": sorted(scope), "active_scope": sorted(used), "summary_group": group}


def verify_config(config, active, reader=None, **remote_options):
    active = set(active) | {"root"}
    remote = Remote(reader, **remote_options)
    known = set(PLUGIN_PINS) | set(MAVEN_PINS) | PARAMETERS | DISTRIBUTIONS | {"version", "minecraft_version", "parchment_minecraft"}
    java_keys = {key for key in config if key.endswith("java_version")}
    keys = sorted(known | java_keys | {key for key in config if key.endswith("_version")})
    results = []
    for key in keys:
        sources = ["gradle.properties"]
        entry = {"property": key, "value": config.get(key), "status": "checked", "kind": "publication", "sources": sources}
        entry.update(presentation_scope(key, config, active))
        try:
            scope = PLUGIN_PINS[key][2] if key in PLUGIN_PINS else MAVEN_PINS[key][3] if key in MAVEN_PINS else None
            if key.startswith("minestom_"):
                scope = {"minestom"}
            if key == "parchment_minecraft":
                scope = {"common", "fabric", "neoforge"}
            if scope and not (scope & active):
                entry.update(status="skipped", detail="Target module is absent; its pin is unused.")
            elif key in PARAMETERS or key in java_keys:
                entry.update(status="skipped", kind="parameter", detail="Outside publication lookup: this parameter belongs to the existing scaffold/configuration checks.")
            elif key not in known:
                raise VerificationError("Uncovered version property: add its official metadata mapping.")
            elif key not in config or not config[key]:
                raise VerificationError("Required active version property is missing or empty.")
            elif key == "version":
                entry["kind"] = "structure"
                if not SEMVER.fullmatch(config[key]):
                    raise VerificationError("Project version is not Semantic Versioning 2.0.0.")
                entry["detail"] = "Project version syntax only; no template product artifact was searched."
            elif key in DISTRIBUTIONS:
                entry["detail"] = published_gradle(config, "minestom_" if key.startswith("minestom_") else "", remote, sources)
            elif key in ("minecraft_version", "parchment_minecraft"):
                entry["detail"] = published_minecraft(config, key, remote, sources)
            elif key in PLUGIN_PINS:
                repository, plugin_id, _ = PLUGIN_PINS[key]
                published_pom(remote, sources, repository, plugin_id, plugin_id + ".gradle.plugin", config[key])
                entry["detail"] = "The official plugin repository publishes this marker POM."
            else:
                repository, group, artifact, scope = MAVEN_PINS[key]
                value = config[key]
                fixed_version(value)
                if key in ("forge_version", "neo_form_version"):
                    value = config["minecraft_version"] + "-" + value
                if key == "parchment_version":
                    artifact += config["parchment_minecraft"]
                artifacts = [artifact + target for target in ("common", "fabric", "forge", "neoforge") if target in active] if key == "mixinextras_version" else [artifact]
                if key == "slf4j_version" and "minestom" in active:
                    artifacts.append("slf4j-simple")
                for artifact in artifacts:
                    published_pom(remote, sources, repository, group, artifact, value)
                entry["detail"] = "The official Maven repository publishes the requested POM identity."
        except VerificationError as error:
            entry.update(status=error.status, detail=str(error))
        except (KeyError, TypeError, ValueError) as error:
            entry.update(status="failed", detail=f"Invalid or incomplete publication metadata/configuration: {error}")
        results.append(entry)
    counts = Counter(item["status"] for item in results)
    return {"result": "failed" if counts["failed"] or counts["unverified"] else "passed", "pins": results,
            "counts": dict(counts), "active_modules": sorted(active - {"root"}),
            "limits": ["Only publisher metadata was read; no dependency was downloaded and no build or application was executed.",
                       "Publication existence does not establish Minecraft, Java or runtime compatibility."]}


def markdown_summary(report):
    statuses = {"checked": "✅ Checked", "failed": "❌ Failed",
                "unverified": "⚠️ Unverified", "skipped": "⏩ Skipped"}
    lines = ["### Published version metadata", "", f"Result: **{report['result']}**", ""]
    groups = ("Shared dependencies", "Common", "Fabric", "Forge", "NeoForge", "Minestom", "Build tooling", "Configuration")
    for group in groups:
        entries = [entry for entry in report["pins"] if entry.get("summary_group", "Configuration") == group]
        if not entries:
            continue
        lines.extend([f"#### {group}", "", "| Property | Value | Used by | Status | Detail |",
                      "| --- | --- | --- | --- | --- |"])
        for entry in entries:
            escape = lambda value: str(value).replace("|", "\\|").replace("\n", " ")
            scope = entry.get("active_scope") or entry.get("scope", [])
            consumers = ", ".join(SCOPE_LABELS.get(owner, owner) for owner in scope)
            if scope and not entry.get("active_scope"):
                consumers += " (inactive)"
            values = [entry.get("property", ""), entry.get("value", ""), consumers,
                      statuses.get(entry.get("status"), entry.get("status", "")), entry.get("detail", "")]
            lines.append("| " + " | ".join(escape(value) for value in values) + " |")
        lines.append("")
    if report.get("error"):
        lines.extend(["", "Configuration error: " + str(report["error"]).replace("\n", " ")])
    lines.extend(["", "Metadata only; no dependency download or compatibility claim.", ""])
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--report", type=Path)
    parser.add_argument("--summary", type=Path)
    args = parser.parse_args()
    try:
        config = properties(args.root / "gradle.properties")
        active = {name for name in module_list(config, "modules") if (args.root / name).is_dir()}
        if (args.root / "buildSrc/build.gradle").is_file():
            active.add("buildsrc")
        report = verify_config(config, active)
    except (OSError, ValueError) as error:
        report = {"result": "failed", "pins": [], "counts": {"failed": 1}, "error": str(error)}
    output = json.dumps(report, indent=2)
    print(output)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(output + "\n", encoding="utf-8")
    if args.summary:
        with args.summary.open("a", encoding="utf-8") as summary:
            summary.write(markdown_summary(report))
    raise SystemExit(0 if report["result"] == "passed" else 1)


if __name__ == "__main__":
    main()
