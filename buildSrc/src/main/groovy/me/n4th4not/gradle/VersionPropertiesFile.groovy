package me.n4th4not.gradle

import java.nio.charset.StandardCharsets
import java.nio.file.Files
import java.nio.file.Path
import java.nio.file.StandardCopyOption
import java.util.regex.Matcher
import java.util.regex.Pattern

/** Changes selected version values without rewriting comments or unrelated settings. */
final class VersionPropertiesFile {
    static String replaceVersions(String original, Map<String, String> versions) {
        String result = original
        versions.each { String key, String value ->
            if (!(value ==~ /[A-Za-z0-9.+_-]+/)) {
                throw new IllegalArgumentException("Invalid version for ${key}: ${value}")
            }
            Pattern pattern = Pattern.compile('(?m)^([ \\t]*' + Pattern.quote(key) +
                    '[ \\t]*=[ \\t]*)([^\\r\\n]*?)([ \\t]*\\r?)$')
            Matcher matcher = pattern.matcher(result)
            if (!matcher.find()) {
                throw new IllegalArgumentException("Missing property: ${key}")
            }
            String prefix = matcher.group(1)
            String ending = matcher.group(3)
            if (matcher.find()) {
                throw new IllegalArgumentException("Duplicate property: ${key}")
            }
            result = pattern.matcher(result).replaceFirst(Matcher.quoteReplacement(prefix + value + ending))
        }
        return result
    }

    static boolean writeIfUnchanged(Path target, byte[] expected, String replacement) {
        byte[] updated = replacement.getBytes(StandardCharsets.UTF_8)
        if (!Arrays.equals(Files.readAllBytes(target), expected)) {
            throw new IllegalStateException('gradle.properties changed during lookup; retry after saving your edits.')
        }
        if (Arrays.equals(expected, updated)) {
            return false
        }
        Path temporary = Files.createTempFile(target.toAbsolutePath().parent, '.gradle-version-update-', '.tmp')
        try {
            Files.write(temporary, updated)
            if (Files.getFileStore(target).supportsFileAttributeView('posix')) {
                Files.setPosixFilePermissions(temporary, Files.getPosixFilePermissions(target))
            }
            if (!Arrays.equals(Files.readAllBytes(target), expected)) {
                throw new IllegalStateException('gradle.properties changed during lookup; retry after saving your edits.')
            }
            // Fail without replacing the original if atomic moves are unsupported.
            Files.move(temporary, target, StandardCopyOption.ATOMIC_MOVE, StandardCopyOption.REPLACE_EXISTING)
            return true
        } finally {
            Files.deleteIfExists(temporary)
        }
    }
}
