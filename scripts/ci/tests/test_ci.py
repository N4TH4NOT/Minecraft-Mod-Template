"""Fixtures exercise CI decisions without building or starting an application."""

from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from plan import discover, included_modules, make_plan, repository_type
from validate_template import validate
from verify_results import verify


class ScaffoldFixture(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.write("settings.gradle", "include('common')\ninclude 'fabric'\n")
        for name in ("build.gradle", "common/build.gradle", "fabric/build.gradle", "README.md", "AGENTS.md"):
            self.write(name, "// scaffold\n")
        self.write("gradle.properties", "\n".join([
            "version=1.0.0", "group=example.template", "mod_id=example", "minecraft_version=1.21.10",
            "java_version=21", "minecraft_pack_version=69", "minestom_version=2025.12.19-1.21.10",
            "minestom_java_version=25",
        ]))
        self.write("common/src/main/resources/pack.mcmeta", '{"pack":{"pack_format":${minecraft_pack_version}}}')
        self.write("fabric/src/main/resources/fabric.mod.json", '{"id":"${mod_id}","version":"${version}"}')
        self.write("fabric/src/main/resources/META-INF/services/example.template.Platform", "example.template.FabricPlatform\n")
        self.wrapper("")

    def write(self, path, content):
        file = self.root / path
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(content, encoding="utf-8")
        return file

    def wrapper(self, prefix, version=None):
        directory = self.root / prefix
        version = version or ("9.1.0" if prefix else "8.14.6")
        for name in ("gradlew", "gradlew.bat"):
            self.write(str(Path(prefix) / name), "wrapper script\n")
        self.write(str(Path(prefix) / "gradle/wrapper/gradle-wrapper.properties"),
                   f"distributionUrl=https\\://services.gradle.org/distributions/gradle-{version}-bin.zip\n"
                   "distributionSha256Sum=" + "a" * 64 + "\n")
        with zipfile.ZipFile(directory / "gradle/wrapper/gradle-wrapper.jar", "w") as archive:
            archive.writestr("org/gradle/wrapper/GradleWrapperMain.class", b"fixture")

    def minestom(self):
        self.write("minestom/settings.gradle", "rootProject.name='example-minestom'\n")
        self.write("minestom/build.gradle", "plugins { id 'application' }\n")
        self.wrapper("minestom")


class PlanningTest(ScaffoldFixture):
    def test_template_without_main_or_test_java_never_schedules_builds(self):
        self.minestom()
        self.assertEqual([], list(self.root.rglob("*.java")))
        plan = make_plan(self.root, repository_type("auto", True))
        self.assertEqual({"include": []}, plan["matrix"])
        self.assertFalse(plan["has_builds"])
        self.assertFalse(plan["support_tests"])
        self.assertEqual("passed", validate(self.root)["result"])

    def test_derived_project_without_application_sources_fails(self):
        with self.assertRaisesRegex(ValueError, "no Java application sources"):
            make_plan(self.root, repository_type("auto", False))

    def test_only_configured_targets_are_built_with_their_java_version(self):
        self.write("fabric/src/main/java/example/Main.java", "class Main {}")
        self.write("forge/build.gradle", "// deliberately not included")
        self.minestom()
        matrix = make_plan(self.root, "project")["matrix"]["include"]
        self.assertEqual(["fabric", "minestom"], [row["target"] for row in matrix])
        self.assertEqual(["21", "25"], [row["java"] for row in matrix])
        self.assertTrue(matrix[0]["common"])
        self.assertFalse(matrix[1]["common"])

    def test_dispatch_override_takes_precedence_over_github_metadata(self):
        self.assertEqual("project", repository_type("project", True))
        self.assertEqual("template", repository_type("template", False))
        self.assertEqual("template", repository_type("template", None))

    def test_missing_metadata_is_never_silently_treated_as_a_project(self):
        with self.assertRaisesRegex(ValueError, "is_template is unavailable"):
            repository_type("auto", None)

    def test_comment_and_repository_filters_do_not_declare_modules(self):
        self.write("settings.gradle", "// include('forge')\n/* include('neoforge') */\n"
                   "includeGroup('not-a-project')\ninclude('fabric', 'common')\n")
        self.assertEqual(["common", "fabric"], included_modules(self.root / "settings.gradle"))

    def test_inline_comments_do_not_declare_modules_or_remove_quoted_urls(self):
        self.write("settings.gradle", "include('fabric') // include('forge')\n"
                   "include('common') /* include('neoforge') */\n"
                   "def repository = 'https://example.org'\n")
        self.assertEqual(["common", "fabric"], included_modules(self.root / "settings.gradle"))

    def test_declared_module_without_build_is_an_error(self):
        (self.root / "fabric/build.gradle").unlink()
        with self.assertRaisesRegex(ValueError, "has no build.gradle"):
            discover(self.root)

    def test_minestom_must_not_be_included_in_the_gradle8_root(self):
        self.write("settings.gradle", "include('minestom')\n")
        with self.assertRaisesRegex(ValueError, "standalone build"):
            discover(self.root)

    def test_incomplete_standalone_minestom_build_is_an_error(self):
        self.write("minestom/build.gradle", "// missing its settings.gradle")
        with self.assertRaisesRegex(ValueError, "both minestom/settings.gradle"):
            discover(self.root)


class TemplateValidationTest(ScaffoldFixture):
    def test_declared_service_does_not_require_java_in_a_template(self):
        self.assertEqual("passed", validate(self.root)["result"])

    def test_unknown_resource_property_is_an_error(self):
        self.write("fabric/src/main/resources/fabric.mod.json", '{"id":"${missing_property}"}')
        with self.assertRaisesRegex(ValueError, "undefined property"):
            validate(self.root)

    def test_invalid_service_provider_is_an_error(self):
        self.write("fabric/src/main/resources/META-INF/services/example.template.Platform", "not a class name\n")
        with self.assertRaisesRegex(ValueError, "invalid service provider"):
            validate(self.root)

    def test_distribution_checksum_must_be_declared(self):
        self.write("gradle/wrapper/gradle-wrapper.properties",
                   "distributionUrl=https\\://services.gradle.org/distributions/gradle-8.14.6-bin.zip\n")
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            validate(self.root)

    def test_minestom_must_target_the_same_minecraft_version(self):
        self.minestom()
        properties = self.root / "gradle.properties"
        properties.write_text(properties.read_text().replace("2025.12.19-1.21.10", "2025.12.19-1.21.11"))
        with self.assertRaisesRegex(ValueError, "target minecraft_version"):
            validate(self.root)

    def test_modloader_chain_rejects_a_gradle9_root_wrapper(self):
        self.wrapper("", version="9.1.0")
        with self.assertRaisesRegex(ValueError, "Gradle 8 wrapper"):
            validate(self.root)

    def test_modloader_chain_rejects_java25(self):
        path = self.root / "gradle.properties"
        path.write_text(path.read_text().replace("java_version=21", "java_version=25"))
        with self.assertRaisesRegex(ValueError, "java_version=21"):
            validate(self.root)

    def test_minestom_chain_rejects_wrapper_versions_without_java25_support(self):
        self.minestom()
        for version in ("8.14.6", "9.0.0"):
            with self.subTest(version=version):
                self.wrapper("minestom", version=version)
                with self.assertRaisesRegex(ValueError, "Gradle 9.1 or newer"):
                    validate(self.root)


class ResultsTest(ScaffoldFixture):
    def report(self, name="Example", tests=1, skipped=0, failures=0):
        self.write(f"fabric/build/test-results/test/TEST-{name}.xml",
                   f'<testsuite tests="{tests}" skipped="{skipped}" failures="{failures}" errors="0"/>')

    def test_missing_reports_fail_even_when_test_sources_were_removed(self):
        self.assertEqual([], list((self.root / "fabric").rglob("*.java")))
        with self.assertRaisesRegex(ValueError, "JUnit reports are missing"):
            verify(self.root / "fabric")

    def test_empty_suite_is_not_a_validation(self):
        self.report(tests=0)
        with self.assertRaisesRegex(ValueError, "no tests ran"):
            verify(self.root / "fabric")

    def test_entirely_skipped_suite_is_not_a_validation(self):
        self.report(tests=3, skipped=3)
        with self.assertRaisesRegex(ValueError, "no tests ran"):
            verify(self.root / "fabric")

    def test_failed_test_is_reported_as_a_failure(self):
        self.report(failures=1)
        with self.assertRaisesRegex(ValueError, "test failures"):
            verify(self.root / "fabric")

    def test_reports_count_only_executed_tests(self):
        self.report(name="PartiallySkipped", tests=3, skipped=1)
        self.report(name="Passing", tests=1)
        result = verify(self.root / "fabric")
        self.assertEqual(3, result["executed"])
        self.assertEqual(1, result["skipped"])
        self.assertEqual(2, result["reports"])


if __name__ == "__main__":
    unittest.main()
