"""Fixtures exercise CI decisions without building or starting an application."""

from pathlib import Path
import shutil
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from plan import configured_modules, discover, make_plan, properties, repository_type
from validate_template import validate
from verify_results import verify


class ScaffoldFixture(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.write("settings.gradle", "// Read central gradle.properties\n")
        for name in ("build.gradle", "common/build.gradle", "fabric/build.gradle", "gradle/build-plan.gradle",
                     "gradle/scaffold.gradle", "gradle/bootstrap/settings.gradle", "gradle/bootstrap/build.gradle",
                     "README.md", "AGENTS.md"):
            self.write(name, "// scaffold\n")
        self.write("gradle.properties", "\n".join([
            "version=1.0.0", "group=example.template", "mod_id=example", "minecraft_version=1.21.10",
            "modules=common,fabric,forge,neoforge,minestom", "required_modules=common", "standalone_modules=minestom",
            "java_version=21", "gradle_java_version=21", "minecraft_pack_version=69",
            "gradle_version=8.14.6", "gradle_distribution_sha256=" + "a" * 64,
            "forgegradle_version=6.0.54", "minestom_version=2025.12.19-1.21.10",
            "minestom_java_version=25", "minestom_gradle_java_version=25", "minestom_gradle_version=9.1.0",
            "minestom_gradle_distribution_sha256=" + "a" * 64,
        ]))
        for module in ("common", "fabric", "forge", "neoforge", "minestom"):
            self.write(f"gradle/modules/{module}.gradle", "// central build configuration\n")
        self.write("common/src/main/resources/pack.mcmeta", '{"pack":{"pack_format":${minecraft_pack_version}}}')
        self.write("fabric/src/main/resources/fabric.mod.json", '{"id":"${mod_id}","version":"${version}"}')
        self.write("fabric/src/main/resources/META-INF/services/example.template.Platform", "example.template.FabricPlatform\n")
        self.wrapper("")

    def write(self, path, content):
        file = self.root / path
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(content, encoding="utf-8")
        return file

    def configure(self, **values):
        config = properties(self.root / "gradle.properties")
        config.update(values)
        self.write("gradle.properties", "\n".join(f"{key}={value}" for key, value in config.items()) + "\n")

    def wrapper(self, prefix, version=None, checksum=None):
        directory = self.root / prefix
        config = properties(self.root / "gradle.properties")
        key_prefix = "minestom_" if prefix else ""
        version = version or config[key_prefix + "gradle_version"]
        checksum = checksum or config[key_prefix + "gradle_distribution_sha256"]
        for name in ("gradlew", "gradlew.bat"):
            self.write(str(Path(prefix) / name), "wrapper script\n")
        self.write(str(Path(prefix) / "gradle/wrapper/gradle-wrapper.properties"),
                   f"distributionUrl=https\\://services.gradle.org/distributions/gradle-{version}-bin.zip\n"
                   f"distributionSha256Sum={checksum}\n")
        with zipfile.ZipFile(directory / "gradle/wrapper/gradle-wrapper.jar", "w") as archive:
            archive.writestr("org/gradle/wrapper/GradleWrapperMain.class", b"fixture")

    def minestom(self):
        self.write("minestom/settings.gradle", "rootProject.name='example-minestom'\n")
        self.wrapper("minestom")

    def preset(self, module):
        self.write(f"gradle/templates/{module}/src/main/java/example/Bootstrap.java", "class Bootstrap {}")
        if module == "minestom":
            self.write("gradle/templates/minestom/settings.gradle", "// standalone preset\n")
            self.wrapper("gradle/templates/minestom")
            self.write("gradle/templates/minestom/gradle/wrapper/gradle-wrapper.properties",
                       "distributionUrl=https\\://services.gradle.org/distributions/gradle-__MIN_GRADLE_VERSION__-bin.zip\n"
                       "distributionSha256Sum=__MIN_GRADLE_SHA256__\n")

    def all_targets(self):
        for loader, descriptor in (("forge", "mods.toml"), ("neoforge", "neoforge.mods.toml")):
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

    def test_derived_project_without_application_or_initialization_sources_fails(self):
        with self.assertRaisesRegex(ValueError, "no Java application sources"):
            make_plan(self.root, repository_type("auto", False))

    def test_only_configured_present_targets_are_built(self):
        self.write("fabric/src/main/java/example/Main.java", "class Main {}")
        self.write("discarded/build.gradle", "// absent from central modules property")
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

    def test_module_names_are_read_from_the_central_property(self):
        self.configure(modules="common, fabric")
        self.assertEqual(["common", "fabric"], configured_modules(self.root / "gradle.properties"))

    def test_properties_comments_do_not_declare_modules(self):
        path = self.root / "gradle.properties"
        path.write_text(path.read_text() + "\n# modules=other\n! modules=ignored\n")
        self.assertEqual(["common", "fabric", "forge", "neoforge", "minestom"], configured_modules(path))

    def test_present_module_without_local_or_central_build_is_an_error(self):
        (self.root / "fabric/build.gradle").unlink()
        (self.root / "gradle/modules/fabric.gradle").unlink()
        with self.assertRaisesRegex(ValueError, "neither build.gradle nor a central"):
            discover(self.root)

    def test_minestom_must_be_declared_as_standalone(self):
        self.configure(standalone_modules="")
        with self.assertRaisesRegex(ValueError, "standalone build"):
            discover(self.root)

    def test_incomplete_nonempty_standalone_minestom_is_an_error(self):
        self.write("minestom/.unexpected", "not an empty target")
        with self.assertRaisesRegex(ValueError, "needs settings.gradle"):
            discover(self.root)

    def test_removing_each_target_directory_skips_only_that_target(self):
        self.write("common/src/main/java/example/Shared.java", "class Shared {}")
        for target in ("fabric", "forge", "neoforge", "minestom"):
            with self.subTest(target=target):
                self.all_targets()
                if not (self.root / "fabric").exists():
                    self.write("fabric/src/main/resources/fabric.mod.json", '{"id":"${mod_id}"}')
                shutil.rmtree(self.root / target)
                plan = make_plan(self.root, "project")
                expected = {"fabric", "forge", "neoforge", "minestom"} - {target}
                self.assertEqual(expected, {row["target"] for row in plan["matrix"]["include"]})
                self.assertEqual([target], plan["excluded_modules"])
                self.assertEqual("passed", validate(self.root)["result"])

    def test_removing_multiple_targets_keeps_the_remaining_target(self):
        self.all_targets()
        self.write("common/src/main/java/example/Shared.java", "class Shared {}")
        for target in ("fabric", "forge", "minestom"):
            shutil.rmtree(self.root / target)
        matrix = make_plan(self.root, "project")["matrix"]["include"]
        self.assertEqual(["neoforge"], [row["target"] for row in matrix])
        self.assertEqual("passed", validate(self.root)["result"])

    def test_minestom_only_keeps_required_common(self):
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

    def test_common_must_remain_declared_and_required(self):
        for values in ({"modules": "fabric,minestom"}, {"required_modules": "fabric"}):
            with self.subTest(values=values):
                changed = dict(modules="common,fabric,forge,neoforge,minestom", required_modules="common")
                changed.update(values)
                self.configure(**changed)
                with self.assertRaisesRegex(ValueError, "common module is required"):
                    discover(self.root)

    def test_empty_target_without_initialization_preset_is_an_error(self):
        (self.root / "forge").mkdir()
        with self.assertRaisesRegex(ValueError, "initialization preset"):
            discover(self.root)

    def test_empty_minestom_without_initialization_preset_is_an_error(self):
        (self.root / "minestom").mkdir()
        with self.assertRaisesRegex(ValueError, "initialization preset"):
            discover(self.root)

    def test_custom_modules_can_keep_a_local_build_script(self):
        self.configure(modules="common,fabric,extra/library", standalone_modules="")
        self.write("extra/library/build.gradle", "// custom library\n")
        modules, _ = discover(self.root)
        self.assertEqual(["common", "fabric", "extra/library"], modules)

    def test_invalid_or_duplicate_module_paths_are_rejected(self):
        for paths in ("../outside", "/absolute", "common,common"):
            with self.subTest(paths=paths):
                self.configure(modules=paths)
                with self.assertRaises(ValueError):
                    discover(self.root)

    def test_local_build_is_optional_when_the_central_configuration_exists(self):
        (self.root / "fabric/build.gradle").unlink()
        self.assertIn("fabric", discover(self.root)[0])
        self.assertEqual("passed", validate(self.root)["result"])

    def test_empty_target_uses_a_preset_without_generating_locally(self):
        shutil.rmtree(self.root / "fabric")
        self.write("fabric/.gitkeep", "")
        self.preset("fabric")
        plan = make_plan(self.root, "project")
        self.assertEqual(["fabric"], plan["initialization_modules"])
        self.assertEqual("passed", validate(self.root)["result"])
        self.assertEqual([".gitkeep"], [path.name for path in (self.root / "fabric").iterdir()])

    def test_empty_minestom_uses_preset_wrapper_and_bootstrap_runtime(self):
        (self.root / "minestom").mkdir()
        self.preset("minestom")
        plan = make_plan(self.root, "project")
        row = next(row for row in plan["matrix"]["include"] if row["target"] == "minestom")
        self.assertEqual("21\n25", row["java_versions"])
        self.assertTrue(row["initialize"])
        self.assertEqual("passed", validate(self.root)["result"])
        self.assertEqual([], list((self.root / "minestom").iterdir()))

    def test_module_toolchains_and_gradle_runtime_are_independent(self):
        self.write("fabric/src/main/java/example/Main.java", "class Main {}")
        self.configure(common_java_version="23", fabric_java_version="22", gradle_java_version="21")
        plan = make_plan(self.root, "project")
        row = plan["matrix"]["include"][0]
        self.assertEqual("21", row["java"])
        self.assertEqual("22\n23\n21", row["java_versions"])
        self.assertEqual("23\n21", plan["scaffold_java_versions"])

    def test_standalone_registry_can_be_empty_when_minestom_is_not_selected(self):
        self.configure(modules="common,fabric", standalone_modules="")
        self.assertEqual((["common", "fabric"], False), discover(self.root))

    def test_buildsrc_toolchain_is_installed_alongside_a_distinct_runtime(self):
        self.write("fabric/src/main/java/example/Main.java", "class Main {}")
        self.configure(buildsrc_java_version="21", gradle_java_version="23")
        plan = make_plan(self.root, "project")
        self.assertEqual("21\n23", plan["support_java_versions"])
        self.assertEqual("21\n23", plan["matrix"]["include"][0]["java_versions"])


class TemplateValidationTest(ScaffoldFixture):
    def test_service_declarations_do_not_require_java_in_a_template(self):
        self.assertEqual("passed", validate(self.root)["result"])

    def test_unknown_resource_property_is_an_error(self):
        self.write("fabric/src/main/resources/fabric.mod.json", '{"id":"${missing_property}"}')
        with self.assertRaisesRegex(ValueError, "undefined property"):
            validate(self.root)

    def test_invalid_service_provider_is_an_error(self):
        self.write("fabric/src/main/resources/META-INF/services/example.template.Platform", "not a class name\n")
        with self.assertRaisesRegex(ValueError, "invalid service provider"):
            validate(self.root)

    def test_wrapper_checksum_must_match_the_central_value(self):
        self.wrapper("", checksum="b" * 64)
        with self.assertRaisesRegex(ValueError, "Wrapper SHA-256"):
            validate(self.root)

    def test_central_checksum_must_be_a_sha256(self):
        self.configure(gradle_distribution_sha256="not-a-checksum")
        with self.assertRaisesRegex(ValueError, "must be a SHA-256"):
            validate(self.root)

    def test_minestom_must_target_the_same_minecraft_version(self):
        self.minestom()
        self.configure(minestom_version="2025.12.19-1.21.11")
        with self.assertRaisesRegex(ValueError, "target minecraft_version"):
            validate(self.root)

    def test_wrapper_version_must_match_the_central_value(self):
        self.wrapper("", version="9.1.0")
        with self.assertRaisesRegex(ValueError, "differs from central gradle_version"):
            validate(self.root)

    def test_root_runtime_must_be_supported_by_its_gradle_version(self):
        self.configure(gradle_java_version="25")
        with self.assertRaisesRegex(ValueError, "runtime requires Gradle 9.1"):
            validate(self.root)

    def test_root_toolchains_must_be_supported_by_their_gradle_version(self):
        self.configure(fabric_java_version="25")
        with self.assertRaisesRegex(ValueError, "toolchain requires Gradle 9.1"):
            validate(self.root)

    def test_buildsrc_bytecode_must_be_loadable_by_the_gradle_runtime(self):
        self.configure(buildsrc_java_version="23", gradle_java_version="21")
        with self.assertRaisesRegex(ValueError, "must load the buildSrc bytecode"):
            validate(self.root)

    def test_minestom_runtime_and_toolchain_chain_are_checked(self):
        self.minestom()
        for value in ("8.14.6", "9.0.0"):
            with self.subTest(value=value):
                self.configure(minestom_gradle_version=value)
                self.wrapper("minestom")
                with self.assertRaisesRegex(ValueError, "requires Gradle 9.1"):
                    validate(self.root)

    def test_forgegradle6_rejects_gradle9_when_forge_is_present(self):
        self.all_targets()
        self.configure(gradle_version="9.1.0")
        self.wrapper("")
        with self.assertRaisesRegex(ValueError, "ForgeGradle 6"):
            validate(self.root)

    def test_invalid_central_version_is_not_accepted(self):
        self.configure(gradle_version="latest")
        with self.assertRaisesRegex(ValueError, "stable Gradle version"):
            validate(self.root)

    def test_non_numeric_java_configuration_is_not_accepted(self):
        self.configure(java_version="latest")
        with self.assertRaisesRegex(ValueError, "positive Java language version"):
            validate(self.root)

    def test_minestom_release_minimum_java_version_is_checked(self):
        self.minestom()
        self.configure(minestom_java_version="21")
        with self.assertRaisesRegex(ValueError, "toolchain of at least 25"):
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
