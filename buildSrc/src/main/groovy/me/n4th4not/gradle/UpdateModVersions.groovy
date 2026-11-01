package me.n4th4not.gradle

import org.gradle.api.DefaultTask
import org.gradle.api.file.RegularFileProperty
import org.gradle.api.tasks.Input
import org.gradle.api.tasks.InputFile
import org.gradle.api.tasks.PathSensitive
import org.gradle.api.tasks.PathSensitivity
import org.gradle.api.tasks.TaskAction
import org.gradle.work.DisableCachingByDefault

@DisableCachingByDefault(because = 'Checks live release metadata only when explicitly invoked')
abstract class UpdateModVersions extends DefaultTask {
    @InputFile
    @PathSensitive(PathSensitivity.RELATIVE)
    abstract RegularFileProperty getPropertiesFile()

    @Input
    boolean applyUpdates = false

    @Input
    boolean offlineMode = false

    @TaskAction
    void updateVersions() {
        ModVersionUpdate.execute(propertiesFile.get().asFile, applyUpdates, offlineMode, logger)
    }
}
