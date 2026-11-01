package me.n4th4not.gradle

import org.gradle.api.GradleException
import org.gradle.api.logging.Logger

import java.nio.charset.StandardCharsets
import java.nio.file.Files

final class ModVersionUpdate {
    static Map<String, String> execute(File propertiesFile, boolean applyUpdates, boolean offline, Logger logger) {
        if (offline) {
            throw new GradleException('Version lookup requires network access; remove --offline.')
        }
        def path = propertiesFile.toPath()
        byte[] originalBytes = Files.readAllBytes(path)
        String original = new String(originalBytes, StandardCharsets.UTF_8)
        Properties current = new Properties()
        current.load(new StringReader(original))

        Map<String, String> versions
        try {
            versions = ModDependencyVersions.resolve(current, ModVersionUpdate.&readMetadata)
        } catch (Exception failure) {
            throw new GradleException('Unable to resolve compatible versions; gradle.properties was not changed. ' +
                    failure.message, failure)
        }
        String updated = VersionPropertiesFile.replaceVersions(original, versions)
        logger.lifecycle('Minecraft {} — compatible stable releases:', current.getProperty('minecraft_version'))
        versions.each { key, value ->
            String before = current.getProperty(key)
            logger.lifecycle('  {}: {}{}', key, before, before == value ? ' (unchanged)' : " -> ${value}")
        }
        if (!applyUpdates) {
            logger.lifecycle('Preview only. Run updateModVersions to apply these changes.')
            return versions
        }
        if (VersionPropertiesFile.writeIfUnchanged(path, originalBytes, updated)) {
            logger.lifecycle('Updated gradle.properties. Reload the Gradle project in IntelliJ before building.')
        } else {
            logger.lifecycle('All versions are already current; no file was written.')
        }
        return versions
    }

    private static String readMetadata(String address) {
        URL url = new URI(address).toURL()
        for (int redirects = 0; redirects < 6; redirects++) {
            if (url.protocol != 'https') {
                throw new IOException('Release metadata must use HTTPS.')
            }
            HttpURLConnection connection = (HttpURLConnection) url.openConnection()
            connection.instanceFollowRedirects = false
            connection.connectTimeout = 15000
            connection.readTimeout = 30000
            connection.setRequestProperty('User-Agent',
                    'Mozilla/5.0 (compatible; Minecraft-Mod-Template-Updater/1.0; https://github.com/N4TH4NOT/Minecraft-Mod-Template)')
            connection.setRequestProperty('Accept', 'application/json, application/xml, text/xml')
            try {
                int status = connection.responseCode
                if (status in [301, 302, 303, 307, 308]) {
                    String destination = connection.getHeaderField('Location')
                    if (!destination) {
                        throw new IOException("Missing redirect destination for ${url}")
                    }
                    url = new URI(url.toString()).resolve(destination).toURL()
                    continue
                }
                if (status == 404) {
                    throw new FileNotFoundException("No release metadata at ${url}")
                }
                if (status != 200) {
                    throw new IOException("HTTP ${status} while reading ${url}")
                }
                return connection.inputStream.withCloseable { stream ->
                    byte[] content = stream.readNBytes(8 * 1024 * 1024 + 1)
                    if (content.length > 8 * 1024 * 1024) {
                        throw new IOException("Release metadata exceeds the size limit: ${url}")
                    }
                    new String(content, StandardCharsets.UTF_8)
                }
            } finally {
                connection.disconnect()
            }
        }
        throw new IOException("Too many redirects while reading ${address}")
    }
}
