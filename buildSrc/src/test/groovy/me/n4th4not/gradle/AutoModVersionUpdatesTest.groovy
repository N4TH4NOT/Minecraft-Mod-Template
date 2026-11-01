package me.n4th4not.gradle

import org.junit.jupiter.api.Test

import static org.junit.jupiter.api.Assertions.*

class AutoModVersionUpdatesTest {

    @Test
    void disabledUpdatesLeaveBuildAndTestInvocationsUnchanged() {
        ['build', 'test', 'compileJava', ':fabric:test', 'customCiBuild'].each { String task ->
            assertFalse(AutoModVersionUpdates.shouldUpdate('false', [task]), task)
        }
    }

    @Test
    void enabledUpdatesApplyToBuildTestCompileAndCustomConstructionTasks() {
        ['build', 'test', 'compileJava', ':fabric:test', ':neoforge:build', 'customCiBuild'].each { String task ->
            assertTrue(AutoModVersionUpdates.shouldUpdate('true', [task]), task)
        }
        assertTrue(AutoModVersionUpdates.shouldUpdate('true', ['clean', ':forge:build']))
    }

    @Test
    void informationalAndManualInvocationsDoNotTriggerAutomaticNetworkLookups() {
        ['clean', 'help', 'tasks', 'projects', 'properties', 'dependencies', 'dependencyInsight',
         'buildEnvironment', 'javaToolchains', 'wrapper', 'checkModUpdates', 'updateModVersions'].each { String task ->
            assertFalse(AutoModVersionUpdates.shouldUpdate('true', [task]), task)
        }
        assertFalse(AutoModVersionUpdates.shouldUpdate('true', []))
        assertFalse(AutoModVersionUpdates.shouldUpdate('true', ['clean', 'help', ':fabric:tasks']))
        assertFalse(AutoModVersionUpdates.shouldUpdate('true', ['checkModUpdates', 'updateModVersions']))
    }

    @Test
    void malformedBooleanValuesAreRejectedRatherThanSilentlyDisablingUpdates() {
        ['', 'TRUE', '1', 'yes', null].each { String flag ->
            assertThrows(IllegalArgumentException) {
                AutoModVersionUpdates.shouldUpdate(flag, ['build'])
            }
        }
    }

    @Test
    void manualVersionLookupsCannotBeCombinedWithAlreadyConfiguredBuilds() {
        ['true', 'false'].each { String flag ->
            ['updateModVersions', 'checkModUpdates', ':updateModVersions'].each { String manualTask ->
                assertThrows(IllegalArgumentException) {
                    AutoModVersionUpdates.shouldUpdate(flag, [manualTask, ':fabric:build'])
                }
            }
        }
    }
}
