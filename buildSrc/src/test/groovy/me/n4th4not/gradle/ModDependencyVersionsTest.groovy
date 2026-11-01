package me.n4th4not.gradle

import groovy.json.JsonOutput
import org.junit.jupiter.api.Test

import static org.junit.jupiter.api.Assertions.*

class ModDependencyVersionsTest {

    @Test
    void resolvesTheLatestStableVersionsForTheConfiguredMinecraftOnly() {
        Properties current = properties()
        Properties original = (Properties) current.clone()

        Map<String, String> resolved = ModDependencyVersions.resolve(current, reader(fixtures()))

        assertEquals([
                fabric_loader_version: '0.20.10',
                fabric_version       : '0.138.10+1.21.10',
                forge_version        : '60.1.18',
                neoforge_version     : '21.10.64',
                neo_form_version     : '20251010.172816',
                parchment_minecraft  : '1.21.10',
                parchment_version    : '2025.10.12',
                cloth_config_version : '20.0.149',
                modmenu_version      : '16.0.1'
        ], resolved)
        assertEquals(original, current, 'Resolving updates must not mutate loaded properties')
    }

    @Test
    void rechecksModrinthMinecraftLoaderAndReleaseMetadataAndMavenAvailability() {
        Map<String, String> documents = fixtures()
        documents['cloth-modrinth'] = JsonOutput.toJson([
                release('20.0.149'),
                release('20.0.150', ['1.21.11']),
                release('20.0.151', ['1.21.10'], ['neoforge']),
                release('20.0.152', ['1.21.10'], ['fabric'], 'beta'),
                release('20.0.153'), // Compatible declaration, but not available from the configured Maven.
                release('21.11.160', ['1.21.11'])
        ])
        documents['modmenu-modrinth'] = JsonOutput.toJson([
                release('16.0.1'),
                release('16.0.2', ['1.21.11']),
                release('16.0.3'), // Missing Maven artifact.
                release('17.0.0', ['1.21.11'])
        ])

        Map<String, String> resolved = ModDependencyVersions.resolve(properties(), reader(documents))

        assertEquals('20.0.149', resolved.cloth_config_version)
        assertEquals('16.0.1', resolved.modmenu_version)
    }

    @Test
    void retainsTheConfiguredParchmentTargetWhenTheGameHasNoExactMappingsYet() {
        Properties current = properties()
        current.setProperty('parchment_minecraft', '1.21.9')
        Map<String, String> documents = fixtures()
        documents['parchment-1.21.10'] = xml([])
        documents['parchment-1.21.9'] = xml(['2025.09.30', '2025.10.05', '2025.10.06-SNAPSHOT'])

        Map<String, String> resolved = ModDependencyVersions.resolve(current, reader(documents))

        assertEquals('1.21.9', resolved.parchment_minecraft)
        assertEquals('2025.10.05', resolved.parchment_version)
    }

    @Test
    void fallsBackForMissingParchmentArtifactsButNotForAnUnavailableRepository() {
        Map<String, String> documents = fixtures()
        Closure<String> available = reader(documents)

        Map<String, String> resolved = ModDependencyVersions.resolve(properties(), { String url ->
            if (url.contains('/parchment-1.21.10/')) throw new FileNotFoundException('HTTP 404')
            available.call(url)
        })
        assertEquals('1.21.9', resolved.parchment_minecraft)
        assertEquals('2025.10.05', resolved.parchment_version)

        assertThrows(Exception) {
            ModDependencyVersions.resolve(properties(), { String url ->
                if (url.contains('/parchment-1.21.10/')) throw new IOException('HTTP 503')
                available.call(url)
            })
        }
    }

    @Test
    void neverPreservesNewerVersionsThatBelongToADifferentMinecraftTarget() {
        [
                fabric_version      : '0.140.0+1.21.11',
                forge_version       : '61.0.0',
                neoforge_version    : '21.11.1',
                cloth_config_version: '21.11.160',
                modmenu_version     : '17.0.0'
        ].each { String key, String incompatible ->
            Properties current = properties()
            current.setProperty(key, incompatible)
            Properties original = (Properties) current.clone()

            assertThrows(IllegalStateException) {
                ModDependencyVersions.resolve(current, reader(fixtures()))
            }
            assertEquals(original, current, 'An unverified downgrade must abort without changing properties')
        }
    }

    @Test
    void resolvingAlreadyCurrentVersionsIsIdempotent() {
        Properties current = properties()
        Map<String, String> first = ModDependencyVersions.resolve(current, reader(fixtures()))
        first.each { String key, String value -> current.setProperty(key, value) }

        assertEquals(first, ModDependencyVersions.resolve(current, reader(fixtures())))
    }

    @Test
    void abortsResolutionInsteadOfReturningAPartialUpdateWhenATargetHasNoRelease() {
        Properties current = properties()
        Properties original = (Properties) current.clone()
        Map<String, String> documents = fixtures()
        documents.forge = xml(['1.21.11-61.0.0', '1.21.10-60.2.0-beta'])

        assertThrows(RuntimeException) {
            ModDependencyVersions.resolve(current, reader(documents))
        }
        assertEquals(original, current)
    }

    @Test
    void propagatesNetworkFailuresWithoutChangingProperties() {
        Properties current = properties()
        Properties original = (Properties) current.clone()

        assertThrows(Exception) {
            ModDependencyVersions.resolve(current, { String url ->
                throw new IOException('Simulated request failure')
            })
        }
        assertEquals(original, current)
    }

    @Test
    void rejectsMalformedMetadataInsteadOfChoosingAnUnverifiedVersion() {
        Map<String, String> documents = fixtures()
        documents['fabric-loader'] = '<metadata><versioning>'

        assertThrows(Exception) {
            ModDependencyVersions.resolve(properties(), reader(documents))
        }
    }

    private static Properties properties() {
        Properties properties = new Properties()
        [
                minecraft_version    : '1.21.10',
                fabric_loader_version: '0.17.3',
                fabric_version       : '0.135.0+1.21.10',
                forge_version        : '60.0.3',
                neoforge_version     : '21.10.8-beta',
                neo_form_version     : '20251010.172816',
                parchment_minecraft  : '1.21.9',
                parchment_version    : '2025.10.05',
                cloth_config_version : '20.0.148',
                modmenu_version      : '16.0.0-rc.1'
        ].each { String key, String value -> properties.setProperty(key, value) }
        properties
    }

    private static Map<String, String> fixtures() {
        [
                'fabric-loader'   : xml(['0.20.9', '0.20.10', '0.21.0-beta.1', '0.21.0-SNAPSHOT']),
                'fabric-api'      : xml(['0.138.9+1.21.10', '0.138.10+1.21.10', '0.140.0+1.21.11']),
                'forge'           : xml(['1.21.10-60.1.9', '1.21.10-60.1.18', '1.21.11-61.0.0']),
                'neoforge'        : xml(['21.10.9', '21.10.64', '21.10.65-beta', '21.11.1']),
                'neoform'         : xml(['1.21.10-20251010.172800', '1.21.10-20251010.172816', '1.21.11-20251101.100000']),
                'parchment-1.21.10': xml(['2025.10.05', '2025.10.12', '2025.10.13-SNAPSHOT']),
                'parchment-1.21.9' : xml(['2025.10.05']),
                'cloth-maven'     : xml(['20.0.148', '20.0.149', '20.0.150', '20.0.151', '20.0.152', '21.11.160']),
                'modmenu-maven'   : xml(['16.0.0-rc.1', '16.0.1', '16.0.2', '17.0.0']),
                'cloth-modrinth'  : JsonOutput.toJson([release('20.0.149+fabric'), release('21.11.160', ['1.21.11'])]),
                'modmenu-modrinth': JsonOutput.toJson([release('16.0.1'), release('17.0.0', ['1.21.11'])])
        ]
    }

    private static Closure<String> reader(Map<String, String> documents) {
        { String url ->
            String key
            if (url.contains('api.modrinth.com') && url.contains('/project/cloth-config/')) key = 'cloth-modrinth'
            else if (url.contains('api.modrinth.com') && url.contains('/project/modmenu/')) key = 'modmenu-modrinth'
            else if (url.contains('/fabric-loader/')) key = 'fabric-loader'
            else if (url.contains('/fabric-api/')) key = 'fabric-api'
            else if (url.contains('/net/minecraftforge/forge/')) key = 'forge'
            else if (url.contains('/net/neoforged/neoforge/')) key = 'neoforge'
            else if (url.contains('/net/neoforged/neoform/')) key = 'neoform'
            else if (url.contains('/parchment-1.21.10/')) key = 'parchment-1.21.10'
            else if (url.contains('/parchment-1.21.9/')) key = 'parchment-1.21.9'
            else if (url.contains('/cloth-config-fabric/')) key = 'cloth-maven'
            else if (url.contains('/modmenu/')) key = 'modmenu-maven'
            else throw new AssertionError('Unexpected metadata request: ' + url)
            assertNotNull(documents[key], 'Missing fixture for ' + key)
            documents[key]
        }
    }

    private static String xml(List<String> versions) {
        '<metadata><versioning><versions>' + versions.collect { '<version>' + it + '</version>' }.join() +
                '</versions></versioning></metadata>'
    }

    private static Map release(String version, List<String> games = ['1.21.10'],
                               List<String> loaders = ['fabric'], String type = 'release') {
        [version_number: version, game_versions: games, loaders: loaders, version_type: type]
    }
}
