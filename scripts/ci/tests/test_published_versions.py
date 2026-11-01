"""Publication fixtures use an injected metadata reader and never access the network."""

from http.client import IncompleteRead
import json
from pathlib import Path
import ssl
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from validate_published_versions import (
    CENTRAL, FABRIC, MOJANG, PORTAL, Remote, Response, VerificationError,
    fixed_version, markdown_summary, maven_url, published_minecraft, published_pom, verify_config,
)


class FakeReader:
    def __init__(self):
        self.responses = {}
        self.calls = []

    def add(self, url, body=b"", status=200, content_type="application/xml"):
        if isinstance(body, str):
            body = body.encode()
        self.responses[url] = Response(status, body, content_type)

    def __call__(self, url):
        self.calls.append(url)
        response = self.responses.get(url, Response(404))
        if isinstance(response, list):
            response = response.pop(0) if len(response) > 1 else response[0]
        if isinstance(response, Exception):
            raise response
        return response


def pom(group, artifact, version, packaging="jar"):
    return ('<project xmlns="http://maven.apache.org/POM/4.0.0">'
            f"<groupId>{group}</groupId><artifactId>{artifact}</artifactId><version>{version}</version>"
            f"<packaging>{packaging}</packaging></project>")


def publish(reader, repository, group, artifact, version, packaging="jar"):
    url = maven_url(repository, group, artifact, version)
    reader.add(url, pom(group, artifact, version, packaging))
    return url


class MetadataReaderTest(unittest.TestCase):
    def test_404_is_missing_without_retry(self):
        reader = FakeReader()
        with self.assertRaises(VerificationError) as error:
            Remote(reader, pause=lambda _: None).get("https://publisher.invalid/missing.pom")
        self.assertEqual("failed", error.exception.status)
        self.assertIn("HTTP 404", str(error.exception))
        self.assertEqual(1, len(reader.calls))

    def test_429_and_5xx_are_unverified_after_bounded_retries(self):
        for status in (429, 500, 503):
            with self.subTest(status=status):
                reader = FakeReader()
                reader.add("https://publisher.invalid/metadata", status=status)
                with self.assertRaises(VerificationError) as error:
                    Remote(reader, attempts=2, pause=lambda _: None).get("https://publisher.invalid/metadata")
                self.assertEqual("unverified", error.exception.status)
                self.assertNotIn("not found", str(error.exception))
                self.assertEqual(2, len(reader.calls))

    def test_transient_response_can_recover(self):
        reader = FakeReader()
        url = "https://publisher.invalid/metadata"
        reader.responses[url] = [Response(503), Response(200, b"metadata", "text/plain")]
        self.assertEqual(b"metadata", Remote(reader, pause=lambda _: None).get(url))
        self.assertEqual(2, len(reader.calls))

    def test_timeout_and_truncated_response_remain_unverified(self):
        for problem in (TimeoutError("timed out"), IncompleteRead(b"partial", 20)):
            with self.subTest(problem=problem):
                reader = FakeReader()
                reader.responses["https://publisher.invalid/metadata"] = problem
                with self.assertRaises(VerificationError) as error:
                    Remote(reader, attempts=2, pause=lambda _: None).get("https://publisher.invalid/metadata")
                self.assertEqual("unverified", error.exception.status)
                self.assertEqual(2, len(reader.calls))

    def test_tls_error_is_not_a_missing_version_and_is_not_retried(self):
        reader = FakeReader()
        reader.responses["https://publisher.invalid/metadata"] = ssl.SSLError("certificate rejected")
        with self.assertRaises(VerificationError) as error:
            Remote(reader, pause=lambda _: None).get("https://publisher.invalid/metadata")
        self.assertEqual("unverified", error.exception.status)
        self.assertEqual(1, len(reader.calls))

    def test_html_200_is_not_publication_metadata(self):
        reader = FakeReader()
        url = "https://publisher.invalid/library.pom"
        reader.add(url, "<html>login</html>", content_type="text/html")
        with self.assertRaisesRegex(VerificationError, "HTML"):
            Remote(reader).get(url)

    def test_cache_is_per_run_and_expires(self):
        reader = FakeReader()
        url = "https://publisher.invalid/metadata"
        reader.add(url, "metadata")
        now = [1]
        remote = Remote(reader, ttl=5, clock=lambda: now[0])
        remote.get(url)
        remote.get(url)
        self.assertEqual(1, len(reader.calls))
        now[0] = 7
        remote.get(url)
        self.assertEqual(2, len(reader.calls))
        Remote(reader).get(url)
        self.assertEqual(3, len(reader.calls))


class PublicationMetadataTest(unittest.TestCase):
    def test_parent_group_and_version_confirm_gson_identity(self):
        reader = FakeReader()
        url = maven_url(CENTRAL, "com.google.code.gson", "gson", "2.15.0")
        reader.add(url, '<project xmlns="http://maven.apache.org/POM/4.0.0"><parent><groupId>com.google.code.gson</groupId><artifactId>gson-parent</artifactId><version>2.15.0</version></parent><artifactId>gson</artifactId></project>')
        published_pom(Remote(reader), [], CENTRAL, "com.google.code.gson", "gson", "2.15.0")
        self.assertEqual([url], reader.calls)

    def test_valid_http_response_with_wrong_or_malformed_pom_is_rejected(self):
        for body in ("<project>", "<html/>", pom("wrong.group", "library", "1.0.0"), pom("example", "library", "1.0.1")):
            with self.subTest(body=body):
                reader = FakeReader()
                reader.add(maven_url(CENTRAL, "example", "library", "1.0.0"), body)
                with self.assertRaises(VerificationError):
                    published_pom(Remote(reader), [], CENTRAL, "example", "library", "1.0.0")

    def test_pom_publication_suffices_without_fetching_the_dependency(self):
        reader = FakeReader()
        url = publish(reader, "https://maven.shedaniel.me/", "me.shedaniel.cloth", "cloth-config-fabric", "20.0.149", packaging="pom")
        published_pom(Remote(reader), [], "https://maven.shedaniel.me/", "me.shedaniel.cloth", "cloth-config-fabric", "20.0.149")
        self.assertEqual([url], reader.calls)

    def test_fixed_published_prerelease_is_allowed(self):
        reader = FakeReader()
        publish(reader, CENTRAL, "example", "library", "1.0.0-rc.1")
        published_pom(Remote(reader), [], CENTRAL, "example", "library", "1.0.0-rc.1")

    def test_dynamic_and_mutable_selectors_are_not_publication_pins(self):
        for value in ("latest.release", "+", "1.+", "[1.0,2.0)", "1.0-SNAPSHOT"):
            with self.subTest(value=value):
                with self.assertRaises(VerificationError):
                    fixed_version(value)
        for value in ("21.10.8-beta", "16.0.0-rc.1", "0.138.4+1.21.10", "2025.12.19-1.21.10"):
            fixed_version(value)

    def test_minecraft_confirmation_uses_only_the_official_manifest(self):
        reader = FakeReader()
        reader.add(MOJANG, json.dumps({"versions": [{"id": "1.21.10", "url": "https://piston-meta.mojang.com/version.json"}]}), content_type="application/json")
        published_minecraft({"minecraft_version": "1.21.10"}, "minecraft_version", Remote(reader), [])
        self.assertEqual([MOJANG], reader.calls)

    def test_absent_minecraft_version_and_malformed_manifest_fail(self):
        for body in ('{"versions":[{"id":"1.21.11"}]}', '{"versions":null}', '{"versions":', "[]"):
            with self.subTest(body=body):
                reader = FakeReader()
                reader.add(MOJANG, body, content_type="application/json")
                with self.assertRaises(VerificationError):
                    published_minecraft({"minecraft_version": "1.21.10"}, "minecraft_version", Remote(reader), [])


class PublicationCatalogTest(unittest.TestCase):
    def baseline(self):
        config = {"version": "1.0.0", "minecraft_version": "1.21.10", "minecraft_version_range": "[1.21.10,1.21.11)",
                  "minecraft_pack_version": "69", "minecraft_data_version": "88", "java_version": "21", "gradle_java_version": "21",
                  "gradle_version": "8.14.6", "gradle_distribution_sha256": "a" * 64, "foojay_resolver_version": "1.0.0"}
        reader = FakeReader()
        reader.add(MOJANG, json.dumps({"versions": [{"id": "1.21.10"}]}), content_type="application/json")
        reader.add("https://services.gradle.org/distributions/gradle-8.14.6-bin.zip.sha256", "a" * 64 + "\n", content_type="text/plain")
        publish(reader, PORTAL, "org.gradle.toolchains.foojay-resolver-convention", "org.gradle.toolchains.foojay-resolver-convention.gradle.plugin", "1.0.0", packaging="pom")
        return config, reader

    def test_metadata_catalog_passes_without_any_binary_or_compatibility_lookup(self):
        config, reader = self.baseline()
        report = verify_config(config, set(), reader, pause=lambda _: None)
        self.assertEqual("passed", report["result"])
        self.assertTrue(all(url.endswith((".pom", ".json", ".sha256")) for url in reader.calls))
        self.assertFalse(any(url.endswith((".jar", ".zip", ".module")) or "modrinth" in url for url in reader.calls))
        pins = {pin["property"]: pin for pin in report["pins"]}
        self.assertEqual("skipped", pins["java_version"]["status"])
        self.assertEqual("parameter", pins["minecraft_pack_version"]["kind"])
        self.assertEqual("skipped", pins["minecraft_version_range"]["status"])

    def test_absent_target_pin_is_skipped_without_requesting_its_repository(self):
        config, reader = self.baseline()
        config["forge_version"] = "60.1.18"
        report = verify_config(config, set(), reader, pause=lambda _: None)
        pin = next(pin for pin in report["pins"] if pin["property"] == "forge_version")
        self.assertEqual("skipped", pin["status"])
        self.assertFalse(any("maven.minecraftforge.net" in url for url in reader.calls))

    def test_unknown_version_property_is_an_explicit_error(self):
        config, reader = self.baseline()
        config["new_library_version"] = "1.0.0"
        report = verify_config(config, set(), reader, pause=lambda _: None)
        pin = next(pin for pin in report["pins"] if pin["property"] == "new_library_version")
        self.assertEqual("failed", pin["status"])
        self.assertIn("mapping", pin["detail"])
        self.assertEqual("failed", report["result"])

    def test_network_error_is_not_reported_as_version_absence(self):
        config, reader = self.baseline()
        reader.add(MOJANG, status=503)
        report = verify_config(config, set(), reader, attempts=2, pause=lambda _: None)
        pin = next(pin for pin in report["pins"] if pin["property"] == "minecraft_version")
        self.assertEqual("unverified", pin["status"])
        self.assertEqual("failed", report["result"])

    def test_official_gradle_checksum_must_match_without_fetching_the_archive(self):
        config, reader = self.baseline()
        config["gradle_distribution_sha256"] = "b" * 64
        report = verify_config(config, set(), reader, pause=lambda _: None)
        pins = {pin["property"]: pin for pin in report["pins"]}
        self.assertEqual("failed", pins["gradle_version"]["status"])
        self.assertEqual("failed", pins["gradle_distribution_sha256"]["status"])
        self.assertFalse(any(url.endswith(".zip") for url in reader.calls))

    def test_plugin_marker_is_sufficient_no_implementation_lookup(self):
        config, reader = self.baseline()
        report = verify_config(config, set(), reader, pause=lambda _: None)
        pin = next(pin for pin in report["pins"] if pin["property"] == "foojay_resolver_version")
        self.assertEqual("checked", pin["status"])
        self.assertEqual(1, sum("plugins.gradle.org" in url for url in reader.calls))

    def test_product_semver_is_structure_only_and_configuration_stays_unchanged(self):
        config, reader = self.baseline()
        config["version"] = "0.2.0-rc.1+build.2"
        original = dict(config)
        active = set()
        report = verify_config(config, active, reader, pause=lambda _: None)
        pin = next(pin for pin in report["pins"] if pin["property"] == "version")
        self.assertEqual("checked", pin["status"])
        self.assertEqual("structure", pin["kind"])
        self.assertEqual(original, config)
        self.assertEqual(set(), active)
        self.assertFalse(any("0.2.0-rc.1" in url for url in reader.calls))

    def test_mixinextras_confirms_only_the_present_module_coordinates(self):
        config, reader = self.baseline()
        config["mixinextras_version"] = "0.5.5"
        common = publish(reader, CENTRAL, "io.github.llamalad7", "mixinextras-common", "0.5.5")
        fabric = publish(reader, CENTRAL, "io.github.llamalad7", "mixinextras-fabric", "0.5.5")
        report = verify_config(config, {"common", "fabric"}, reader, pause=lambda _: None)
        pin = next(pin for pin in report["pins"] if pin["property"] == "mixinextras_version")
        self.assertEqual("checked", pin["status"])
        self.assertIn(common, reader.calls)
        self.assertIn(fabric, reader.calls)
        self.assertFalse(any("mixinextras-forge" in url or "mixinextras-neoforge" in url for url in reader.calls))

    def test_shared_test_logging_api_and_minestom_provider_are_confirmed(self):
        config, reader = self.baseline()
        config["slf4j_version"] = "2.0.17"
        api = publish(reader, CENTRAL, "org.slf4j", "slf4j-api", "2.0.17")
        provider = publish(reader, CENTRAL, "org.slf4j", "slf4j-simple", "2.0.17")
        report = verify_config(config, {"common", "minestom"}, reader, pause=lambda _: None)
        pin = next(pin for pin in report["pins"] if pin["property"] == "slf4j_version")
        self.assertEqual("checked", pin["status"])
        self.assertIn(api, reader.calls)
        self.assertIn(provider, reader.calls)

    def test_scopes_use_actual_consumers_and_distinguish_common_from_shared(self):
        config, reader = self.baseline()
        report = verify_config(config, {"common", "fabric", "minestom", "buildsrc"}, reader, pause=lambda _: None)
        pins = {pin["property"]: pin for pin in report["pins"]}
        self.assertEqual(["common", "forge"], pins["mixin_version"]["scope"])
        self.assertEqual(["common"], pins["mixin_version"]["active_scope"])
        self.assertEqual("Common", pins["mixin_version"]["summary_group"])
        self.assertEqual("Shared dependencies", pins["gson_version"]["summary_group"])
        self.assertEqual(["common", "fabric"], pins["gson_version"]["active_scope"])
        self.assertEqual("Minestom", pins["minestom_version"]["summary_group"])
        self.assertEqual("Build tooling", pins["foojay_resolver_version"]["summary_group"])
        self.assertEqual("Configuration", pins["version"]["summary_group"])

    def test_summary_keeps_original_dependency_rows_and_omits_unchecked_parameters(self):
        config, reader = self.baseline()
        config.update(mixinextras_version="0.5.5", minestom_java_version="25")
        for target in ("common", "fabric"):
            publish(reader, CENTRAL, "io.github.llamalad7", "mixinextras-" + target, "0.5.5")
        report = verify_config(config, {"common", "fabric", "minestom"}, reader, pause=lambda _: None)
        summary = markdown_summary(report)
        sections = {part.split("\n", 1)[0]: part for part in summary.split("#### ")[1:]}
        self.assertEqual(1, summary.count("| mixinextras_version |"))
        self.assertIn("| mixinextras_version |", sections["Shared dependencies"])
        self.assertNotIn("| mixinextras_version |", sections["Fabric"])
        self.assertNotIn("mixinextras-fabric", summary)
        self.assertIn("| minestom_version |", sections["Minestom"])
        self.assertIn("❌ Failed", sections["Minestom"])
        self.assertNotIn("| minestom_version |", sections["Shared dependencies"])
        self.assertNotIn("#### Forge\n", summary)
        for key in ("version", "java_version", "minestom_java_version", "minecraft_pack_version",
                    "minecraft_data_version", "minecraft_version_range", "forge_loader_version_range"):
            self.assertNotIn("| " + key + " |", summary)
            self.assertIn(key, {pin["property"] for pin in report["pins"]})

    def test_minestom_gradle_versions_are_grouped_with_minestom(self):
        config, reader = self.baseline()
        config.update(minestom_gradle_version="9.1.0", minestom_gradle_distribution_sha256="b" * 64)
        reader.add("https://services.gradle.org/distributions/gradle-9.1.0-bin.zip.sha256", "b" * 64)
        summary = markdown_summary(verify_config(config, {"common", "minestom"}, reader, pause=lambda _: None))
        sections = {part.split("\n", 1)[0]: part for part in summary.split("#### ")[1:]}
        for key in ("minestom_gradle_version", "minestom_gradle_distribution_sha256"):
            self.assertIn("| " + key + " |", sections["Minestom"])
            self.assertNotIn("| " + key + " |", sections["Build tooling"])
        self.assertIn("| gradle_version |", sections["Build tooling"])

    def test_hidden_configuration_errors_remain_visible_outside_dependency_tables(self):
        config, reader = self.baseline()
        config.update(version="invalid", new_library_version="1.0.0")
        report = verify_config(config, set(), reader, pause=lambda _: None)
        summary = markdown_summary(report)
        self.assertEqual("failed", report["result"])
        self.assertNotIn("| version |", summary)
        self.assertNotIn("| new_library_version |", summary)
        self.assertIn("#### Configuration diagnostics", summary)
        self.assertIn("`version`", summary)
        self.assertIn("`new_library_version`", summary)

    def test_java_gradle_and_range_scopes_describe_their_owners(self):
        config, reader = self.baseline()
        config.update(common_java_version="21", minestom_java_version="25", minestom_gradle_java_version="25",
                      buildsrc_java_version="21")
        report = verify_config(config, {"common", "minestom", "buildsrc"}, reader, pause=lambda _: None)
        pins = {pin["property"]: pin for pin in report["pins"]}
        self.assertEqual(["common"], pins["common_java_version"]["scope"])
        self.assertEqual(["minestom"], pins["minestom_gradle_java_version"]["scope"])
        self.assertEqual(["buildsrc"], pins["buildsrc_java_version"]["scope"])
        self.assertEqual(["root"], pins["gradle_java_version"]["scope"])
        self.assertEqual("Build tooling", pins["minestom_gradle_java_version"]["summary_group"])
        self.assertEqual([], pins["java_version"]["active_scope"])
        self.assertEqual(["forge"], pins["forge_loader_version_range"]["scope"])
        self.assertEqual(["forge", "neoforge"], pins["minecraft_version_range"]["scope"])
        self.assertNotIn("minestom", pins["minecraft_pack_version"]["scope"])


if __name__ == "__main__":
    unittest.main()
