"""Exercise the real Gradle initializer without compiling application sources."""

import os
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest


REPOSITORY = Path(__file__).resolve().parents[3]


class GradleScaffoldTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        shutil.copytree(REPOSITORY / "gradle", self.root / "gradle")
        configuration = (REPOSITORY / "gradle.properties").read_text(encoding="utf-8")
        overrides = {
            "group": "org.example.template",
            "mod_id": "sample",
            "mod_name": 'Sample "Development"',
            "minestom_main_class": "org.example.server.GameServer",
        }
        for key, value in overrides.items():
            configuration, count = re.subn(r"^" + re.escape(key) + r"=.*$",
                                           lambda match: key + "=" + value,
                                           configuration, flags=re.M)
            self.assertEqual(1, count, "The central property must exist: " + key)
        (self.root / "gradle.properties").write_text(configuration, encoding="utf-8")

    def gradle(self, directory, tasks, succeeds=True, configuration_cache=False):
        result = subprocess.run(
            [str(REPOSITORY / "gradlew"), "--no-daemon", "--console=plain",
             "--configuration-cache" if configuration_cache else "--no-configuration-cache",
             "-p", str(directory), *tasks],
            cwd=REPOSITORY, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, timeout=300,
        )
        print(result.stdout)
        if succeeds:
            self.assertEqual(0, result.returncode, result.stdout)
        else:
            self.assertNotEqual(0, result.returncode, result.stdout)
        return result.stdout

    def bootstrap(self, succeeds=True):
        return self.gradle(self.root / "gradle/bootstrap", ["help"], succeeds=succeeds)

    def snapshot(self):
        return {str(path.relative_to(self.root)): path.read_bytes()
                for module in ("common", "fabric", "forge", "neoforge", "minestom")
                for path in (self.root / module).rglob("*") if path.is_file()}

    def test_empty_targets_are_initialized_and_existing_or_absent_targets_are_preserved(self):
        for module in ("common", "forge", "minestom", "fabric"):
            (self.root / module).mkdir()
        (self.root / "common/.gitkeep").write_text("", encoding="utf-8")
        sentinel = self.root / "fabric/owned-by-developer.txt"
        sentinel.write_text("Keep this file unchanged.", encoding="utf-8")

        output = self.bootstrap()
        self.assertIn("Modules vides à initialiser", output)
        self.assertFalse((self.root / "neoforge").exists())
        self.assertEqual([sentinel], list((self.root / "fabric").iterdir()))
        self.assertEqual("Keep this file unchanged.", sentinel.read_text(encoding="utf-8"))
        self.assertTrue((self.root / "common/.gitkeep").is_file())
        constants = self.root / "common/src/main/java/org/example/template/Constants.java"
        self.assertTrue(constants.is_file())
        content = constants.read_text(encoding="utf-8")
        self.assertIn("package org.example.template;", content)
        self.assertIn('"sample"', content)
        self.assertIn(json.dumps('Sample "Development"'), content)
        self.assertTrue((self.root / "forge/src/main/java/org/example/template/ModId.java").is_file())
        self.assertTrue((self.root / "forge/src/main/resources/sample.forge.mixins.json").is_file())
        self.assertTrue((self.root / "minestom/src/main/java/org/example/server/GameServer.java").is_file())
        self.assertTrue((self.root / "minestom/src/test/java/org/example/server/GameServerTest.java").is_file())
        self.assertTrue(os.access(self.root / "minestom/gradlew", os.X_OK))
        wrapper = (self.root / "minestom/gradle/wrapper/gradle-wrapper.properties").read_text()
        self.assertNotIn("__MIN_GRADLE_", wrapper)
        checksum = next(line.split("=", 1)[1] for line in wrapper.splitlines()
                        if line.startswith("distributionSha256Sum="))
        self.assertRegex(checksum, r"^[0-9a-f]{64}$")
        self.assertEqual((REPOSITORY / "gradle/templates/minestom/gradle/wrapper/gradle-wrapper.jar").read_bytes(),
                         (self.root / "minestom/gradle/wrapper/gradle-wrapper.jar").read_bytes())

        constants.write_text(content + "\n// Developer changes are preserved.\n", encoding="utf-8")
        before = self.snapshot()
        second_output = self.bootstrap()
        self.assertNotIn("Modules vides à initialiser", second_output)
        self.assertEqual(before, self.snapshot())

    def test_missing_required_common_fails_before_any_target_is_initialized(self):
        (self.root / "forge").mkdir()
        output = self.bootstrap(succeeds=False)
        self.assertIn("Required module common/", output)
        self.assertEqual([], list((self.root / "forge").iterdir()))
        self.assertFalse((self.root / "common").exists())

    def test_central_builds_exclude_missing_targets_and_report_the_plan_on_cache_reuse(self):
        shutil.copyfile(REPOSITORY / "settings.gradle", self.root / "settings.gradle")
        (self.root / "build.gradle").write_text(
            "apply from: file('gradle/template-properties.gradle')\n"
            "apply from: file('gradle/build-plan.gradle')\n", encoding="utf-8")
        for module in ("common", "fabric"):
            directory = self.root / module
            directory.mkdir()
            (directory / "fixture.txt").write_text("No application sources.\n", encoding="utf-8")
            script = "plugins { id 'java' }\n"
            if module == "fabric":
                script += "tasks.named('compileJava') { dependsOn ':common:compileJava' }\n"
            (self.root / "gradle/modules" / (module + ".gradle")).write_text(script, encoding="utf-8")
        for attempt in range(2):
            with self.subTest(attempt=attempt):
                output = self.gradle(self.root, [":fabric:compileJava"], configuration_cache=True)
                self.assertIn("Modules avec compilation planifiée : common, fabric", output)
                self.assertIn("Modules exclus (dossiers absents)", output)
                self.assertIn("NO-SOURCE", output)
                for excluded in ("forge", "neoforge", "minestom"):
                    self.assertFalse((self.root / excluded).exists())
                if attempt:
                    self.assertIn("Configuration cache entry reused", output)


if __name__ == "__main__":
    unittest.main()
