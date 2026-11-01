package me.n4th4not.gradle

import org.junit.jupiter.api.Test
import org.junit.jupiter.api.io.TempDir

import java.nio.charset.StandardCharsets
import java.nio.file.Files
import java.nio.file.Path
import java.nio.file.attribute.FileTime

import static org.junit.jupiter.api.Assertions.*

class VersionPropertiesFileTest {

    @TempDir
    Path directory

    @Test
    void changesOnlyRequestedVersionsAndPreservesFormattingAndUnicode() {
        String original = '# Dépendances du modèle\r\n' +
                'minecraft_version = 1.21.10\r\n' +
                '  fabric_loader_version\t = \t0.17.3  \r\n' +
                'mod_name=Été et neige ☃\r\n' +
                'fabric_version=0.135.0+1.21.10\r\n' +
                '# fabric_loader_version=ce commentaire reste intact'

        String replacement = VersionPropertiesFile.replaceVersions(original, [
                fabric_loader_version: '0.20.1',
                fabric_version       : '0.138.4+1.21.10'
        ])

        assertEquals(original.replace('\t0.17.3  ', '\t0.20.1  ')
                .replace('fabric_version=0.135.0+1.21.10', 'fabric_version=0.138.4+1.21.10'), replacement)
    }

    @Test
    void refusesMissingDuplicateAndUnsafeValuesRatherThanRewritingAmbiguousProperties() {
        assertThrows(IllegalArgumentException) {
            VersionPropertiesFile.replaceVersions('# fabric_loader_version=0.17.3\n',
                    [fabric_loader_version: '0.20.1'])
        }
        assertThrows(IllegalArgumentException) {
            VersionPropertiesFile.replaceVersions('fabric_loader_version=0.17.3\n  fabric_loader_version=0.18.0\n',
                    [fabric_loader_version: '0.20.1'])
        }
        assertThrows(IllegalArgumentException) {
            VersionPropertiesFile.replaceVersions('fabric_loader_version=0.17.3\n',
                    [fabric_loader_version: '0.20.1\ninjected_property=true'])
        }
    }

    @Test
    void writesTheResolvedVersionsWithoutChangingUnrelatedFileContents() {
        Path target = directory.resolve('gradle.properties')
        String original = '# Versions\nmod_name=Modèle\nminecraft_version=1.21.10\nfabric_loader_version=0.17.3\n'
        byte[] expected = original.getBytes(StandardCharsets.UTF_8)
        Files.write(target, expected)
        String replacement = VersionPropertiesFile.replaceVersions(original, [fabric_loader_version: '0.20.1'])

        assertTrue(VersionPropertiesFile.writeIfUnchanged(target, expected, replacement))

        assertEquals(original.replace('fabric_loader_version=0.17.3', 'fabric_loader_version=0.20.1'),
                Files.readString(target, StandardCharsets.UTF_8))
        try (var files = Files.list(directory)) {
            assertEquals(1L, files.count(), 'Atomic replacement must not leave temporary files behind')
        }
    }

    @Test
    void leavesAnAlreadyCurrentFileUntouched() {
        Path target = directory.resolve('gradle.properties')
        String original = 'fabric_loader_version=0.20.1\n'
        byte[] expected = original.getBytes(StandardCharsets.UTF_8)
        Files.write(target, expected)
        FileTime savedTime = FileTime.fromMillis(1700000000000L)
        Files.setLastModifiedTime(target, savedTime)

        assertFalse(VersionPropertiesFile.writeIfUnchanged(target, expected, original))

        assertArrayEquals(expected, Files.readAllBytes(target))
        assertEquals(savedTime, Files.getLastModifiedTime(target), 'A no-op must not rewrite the file')
    }

    @Test
    void preservesDeveloperEditsMadeWhileVersionsWereBeingResolved() {
        Path target = directory.resolve('gradle.properties')
        byte[] snapshot = 'fabric_loader_version=0.17.3\n'.getBytes(StandardCharsets.UTF_8)
        Files.write(target, snapshot)
        byte[] edited = '# Developer edit\nfabric_loader_version=0.18.0\n'.getBytes(StandardCharsets.UTF_8)
        Files.write(target, edited)

        assertThrows(IllegalStateException) {
            VersionPropertiesFile.writeIfUnchanged(target, snapshot, 'fabric_loader_version=0.20.1\n')
        }

        assertArrayEquals(edited, Files.readAllBytes(target), 'Concurrent edits must not be replaced')
        try (var files = Files.list(directory)) {
            assertEquals(1L, files.count())
        }
    }
}
