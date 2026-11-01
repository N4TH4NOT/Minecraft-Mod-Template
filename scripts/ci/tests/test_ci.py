"""Fixtures exercise CI decisions without building or starting an application."""

from pathlib import Path
import shutil
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from plan import configured_modules, discover, make_plan, repository_type
from validate_template import validate
from verify_results import verify


class ScaffoldFixture(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.write("settings.gradle", "// Read module paths from gradle/modules.txt\n")
        self.write("gradle/modules.txt", "common\nfabric\nforge\nneoforge\n")
        for name in ("build.gradle", "common/build.gradle", "fabric/build.gradle",
                     "gradle/build-plan.gradle", "README.md", "AGENTS.md"):
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

    def all_targets(self):
        for loader, descriptor in (("forge", "mods.toml"), ("neoforge", "neoforge.mods.toml")):
            self.write(f"{loader}/build.gradle", "// scaffold\n")
            self.write(f"{loader}/src/main/resources/META-INF/{descriptor}", 'modId = "${mod_id}"\n')
        self.minestom()


class PlanningTest(ScaffoldFixture):
    def test_template_without_main_or_test_java_never_schedules_builds(self):
        self.minestom()
        self.assertEqual([], list(self.root.rglob("*.java")))
        plan = make_plan(self.root, repository_type("auto", True))
        self.assertEqual({"include": []}, plan["matrix"])
        self.assertFalse(plan["has_builds"])
        self.assertFalse(plan["support_tests"])
        self.assertEqual(["common", "fabric", "minestom"], plan["included_modules"])
        self.assertEqual(["forge", "neoforge"], plan["excluded_modules"])
        self.assertEqual("passed", validate(self.root)["result"])

    def test_derived_project_without_application_sources_fails(self):
        with self.assertRaisesRegex(ValueError, "no Java application sources"):
            make_plan(self.root, repository_type("auto", False))

    def test_only_configured_targets_are_built_with_their_java_version(self):
        self.write("fabric/src/main/java/example/Main.java", "class Main {}")
        self.write("discarded/build.gradle", "// deliberately absent from the module manifest")
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

    def test_manifest_ignores_comments_and_blank_lines(self):
        self.write("gradle/modules.txt", "# forge is optional\n\ncommon\nfabric\n")
        self.assertEqual(["common", "fabric"], configured_modules(self.root / "gradle/modules.txt"))

    def test_manifest_inline_comments_are_not_module_paths(self):
        self.write("gradle/modules.txt", "common # forge\nfabric # neoforge\n")
        self.assertEqual(["common", "fabric"], configured_modules(self.root / "gradle/modules.txt"))

    def test_declared_module_without_build_is_an_error(self):
        (self.root / "fabric/build.gradle").unlink()
        with self.assertRaisesRegex(ValueError, "has no build.gradle"):
            discover(self.root)

    def test_minestom_must_not_be_included_in_the_gradle8_root(self):
        self.write("gradle/modules.txt", "common\nfabric\nminestom\n")
        with self.assertRaisesRegex(ValueError, "standalone build"):
            discover(self.root)

    def test_incomplete_standalone_minestom_build_is_an_error(self):
        self.write("minestom/build.gradle", "// missing its settings.gradle")
        with self.assertRaisesRegex(ValueError, "both minestom/settings.gradle"):
            discover(self.root)

    def test_removing_each_target_directory_skips_only_that_target(self):
        self.write("common/src/main/java/example/Shared.java", "class Shared {}")
        for target in ("fabric", "forge", "neoforge", "minestom"):
            with self.subTest(target=target):
                self.all_targets()
                if not (self.root / "fabric").exists():
                    self.write("fabric/build.gradle", "// scaffold\n")
                    self.write("fabric/src/main/resources/fabric.mod.json", '{"id":"${mod_id}"}')
                shutil.rmtree(self.root / target)
                matrix = make_plan(self.root, "project")["matrix"]["include"]
                expected = {"fabric", "forge", "neoforge", "minestom"} - {target}
                self.assertEqual(expected, {row["target"] for row in matrix})
                self.assertEqual("passed", validate(self.root)["result"])
                self.assertEqual([target], make_plan(self.root, "project")["excluded_modules"])

    def test_removing_multiple_targets_keeps_the_remaining_target(self):
        self.all_targets()
        self.write("common/src/main/java/example/Shared.java", "class Shared {}")
        for target in ("fabric", "forge", "minestom"):
            shutil.rmtree(self.root / target)
        matrix = make_plan(self.root, "project")["matrix"]["include"]
        self.assertEqual(["neoforge"], [row["target"] for row in matrix])
        self.assertEqual("passed", validate(self.root)["result"])

    def test_minestom_only_keeps_required_common_and_removes_modloaders(self):
        self.all_targets()
        for module in ("fabric", "forge", "neoforge"):
            shutil.rmtree(self.root / module)
        self.write("minestom/src/main/java/example/Server.java", "class Server {}")
        matrix = make_plan(self.root, "project")["matrix"]["include"]
        self.assertEqual(["minestom"], [row["target"] for row in matrix])
        self.assertEqual("passed", validate(self.root)["result"])

    def test_removing_required_common_has_a_clear_error(self):
        shutil.rmtree(self.root / "common")
        with self.assertRaisesRegex(ValueError, "common module is required"):
            discover(self.root)

    def test_common_is_required_even_with_only_minestom(self):
        self.minestom()
        shutil.rmtree(self.root / "fabric")
        shutil.rmtree(self.root / "common")
        with self.assertRaisesRegex(ValueError, "common module is required"):
            discover(self.root)

    def test_required_common_must_remain_in_the_shared_manifest(self):
        self.write("gradle/modules.txt", "fabric\n")
        with self.assertRaisesRegex(ValueError, "common module is required"):
            discover(self.root)

    def test_present_empty_modloader_directory_is_an_error(self):
        (self.root / "forge").mkdir()
        with self.assertRaisesRegex(ValueError, "present but has no build.gradle"):
            discover(self.root)

    def test_present_empty_minestom_directory_is_an_error(self):
        (self.root / "minestom").mkdir()
        with self.assertRaisesRegex(ValueError, "both minestom/settings.gradle"):
            discover(self.root)

    def test_new_manifest_modules_can_be_discovered(self):
        self.write("gradle/modules.txt", "common\nfabric\nextra/library\n")
        self.write("extra/library/build.gradle", "// reusable library\n")
        modules, _ = discover(self.root)
        self.assertEqual(["common", "fabric", "extra/library"], modules)

    def test_invalid_or_duplicate_manifest_paths_are_rejected(self):
        for content in ("../outside\n", "/absolute\n", "common\ncommon\n"):
            with self.subTest(content=content):
                self.write("gradle/modules.txt", content)
                with self.assertRaises(ValueError):
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
