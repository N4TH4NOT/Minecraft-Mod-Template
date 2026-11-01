package me.n4th4not.gradle

import groovy.json.JsonOutput
import groovy.json.JsonSlurper
import org.w3c.dom.Element
import org.xml.sax.InputSource

import javax.xml.XMLConstants
import javax.xml.parsers.DocumentBuilderFactory
import java.nio.charset.StandardCharsets

/** Resolves public release metadata without writing files or changing the Minecraft target. */
final class ModDependencyVersions {

    private static final String FABRIC_MAVEN = 'https://maven.fabricmc.net'
    private static final String NEOFORGE_MAVEN = 'https://maven.neoforged.net/releases'

    private ModDependencyVersions() {}

    /**
     * The supplied reader owns HTTP, timeouts and proxy configuration. A missing resource must
     * throw FileNotFoundException; other failures abort the whole resolution, without a fallback.
     */
    static Map<String, String> resolve(Properties current, Closure<String> readText) {
        String minecraft = required(current, 'minecraft_version')
        def minecraftParts = minecraft =~ /^1\.(\d+)(?:\.(\d+))?$/
        if (!minecraftParts.matches()) {
            throw new IllegalArgumentException("Unsupported Minecraft target for NeoForge: ${minecraft}")
        }
        String neoForgePrefix = "${minecraftParts[0][1]}.${minecraftParts[0][2] ?: '0'}."
        Map<String, String> selected = new LinkedHashMap<>()

        selected.fabric_loader_version = latest(
                mavenVersions("${FABRIC_MAVEN}/net/fabricmc/fabric-loader/maven-metadata.xml", readText),
                'Fabric Loader')
        selected.fabric_version = latest(
                mavenVersions("${FABRIC_MAVEN}/net/fabricmc/fabric-api/fabric-api/maven-metadata.xml", readText)
                        .findAll { it.endsWith("+${minecraft}") },
                "Fabric API for Minecraft ${minecraft}")

        String forgePrefix = "${minecraft}-"
        selected.forge_version = latest(
                mavenVersions('https://maven.minecraftforge.net/net/minecraftforge/forge/maven-metadata.xml', readText)
                        .findAll { it.startsWith(forgePrefix) }
                        .collect { it.substring(forgePrefix.length()) },
                "Forge for Minecraft ${minecraft}")
        selected.neoforge_version = latest(
                mavenVersions("${NEOFORGE_MAVEN}/net/neoforged/neoforge/maven-metadata.xml", readText)
                        .findAll { it.startsWith(neoForgePrefix) },
                "NeoForge for Minecraft ${minecraft}")
        selected.neo_form_version = latest(
                mavenVersions("${NEOFORGE_MAVEN}/net/neoforged/neoform/maven-metadata.xml", readText)
                        .findAll { it.startsWith(forgePrefix) }
                        .collect { it.substring(forgePrefix.length()) },
                "NeoForm for Minecraft ${minecraft}")

        Map<String, String> parchment = parchmentVersions(current, minecraft, readText)
        selected.putAll(parchment)

        selected.cloth_config_version = compatibleModVersion(
                'cloth-config', minecraft,
                'https://maven.shedaniel.me/me/shedaniel/cloth/cloth-config-fabric/maven-metadata.xml',
                readText)
        selected.modmenu_version = compatibleModVersion(
                'modmenu', minecraft,
                'https://maven.terraformersmc.com/releases/com/terraformersmc/modmenu/maven-metadata.xml',
                readText)

        // A newer local release may be incompatible, or a mirror may have stale metadata.
        // Neither silently keep an unverified release nor downgrade it: abort before writing.
        // Parchment dates belong to their Minecraft target, so compare dates only within it.
        selected.each { String key, String candidate ->
            String previous = current.getProperty(key)
            boolean sameParchmentTarget = selected.parchment_minecraft == current.getProperty('parchment_minecraft')
            boolean comparable = key != 'parchment_minecraft' &&
                    (key != 'parchment_version' || sameParchmentTarget)
            if (comparable && isStable(previous) && compareVersions(previous, candidate) > 0) {
                throw new IllegalStateException("Cannot verify ${key}=${previous} for Minecraft ${minecraft}: " +
                        "the newest compatible published release is ${candidate}. " +
                        'Check the current version and repository metadata before updating; no versions were changed.')
            }
        }
        return Collections.unmodifiableMap(selected)
    }

    private static Map<String, String> parchmentVersions(Properties current, String minecraft,
                                                         Closure<String> readText) {
        List<String> exactVersions
        try {
            exactVersions = mavenVersions(parchmentMetadata(minecraft), readText).findAll { isStable(it) }
        } catch (FileNotFoundException ignored) {
            exactVersions = []
        }
        if (!exactVersions.isEmpty()) {
            return [parchment_minecraft: minecraft,
                    parchment_version: latest(exactVersions, "Parchment for Minecraft ${minecraft}")]
        }

        String previousTarget = required(current, 'parchment_minecraft')
        if (previousTarget == minecraft || !isStable(previousTarget) ||
                compareVersions(previousTarget, minecraft) > 0) {
            throw new IllegalStateException("No stable Parchment mappings published for Minecraft ${minecraft}")
        }
        List<String> fallback = mavenVersions(parchmentMetadata(previousTarget), readText)
        return [parchment_minecraft: previousTarget,
                parchment_version: latest(fallback, "Parchment for Minecraft ${previousTarget}")]
    }

    private static String parchmentMetadata(String minecraft) {
        return "${NEOFORGE_MAVEN}/org/parchmentmc/data/parchment-${minecraft}/maven-metadata.xml"
    }

    private static String compatibleModVersion(String project, String minecraft, String mavenMetadata,
                                                Closure<String> readText) {
        Set<String> published = new LinkedHashSet<>(mavenVersions(mavenMetadata, readText))
        String gameVersions = URLEncoder.encode(JsonOutput.toJson([minecraft]), StandardCharsets.UTF_8.name())
        String loaders = URLEncoder.encode(JsonOutput.toJson(['fabric']), StandardCharsets.UTF_8.name())
        String url = "https://api.modrinth.com/v2/project/${project}/version?game_versions=${gameVersions}&loaders=${loaders}"
        Object metadata
        try {
            metadata = new JsonSlurper().parseText(readText.call(url))
        } catch (Exception error) {
            throw new IllegalStateException("Cannot read compatible releases from ${url}", error)
        }
        if (!(metadata instanceof List)) {
            throw new IllegalStateException("Invalid Modrinth version list from ${url}")
        }
        List<String> compatible = []
        metadata.each { Object item ->
            if (item instanceof Map && item.version_type == 'release' &&
                    item.game_versions instanceof List && item.game_versions.contains(minecraft) &&
                    item.loaders instanceof List && item.loaders.contains('fabric') &&
                    item.version_number instanceof String) {
                String number = item.version_number
                // Cloth publishes '20.0.149+fabric' on Modrinth and '20.0.149' on Maven.
                String normalized = number.replaceFirst(/(?:\+|-)fabric$/, '')
                String publishedNumber = published.contains(number) ? number : normalized
                if (published.contains(publishedNumber) && isStable(publishedNumber)) {
                    compatible.add(publishedNumber)
                }
            }
        }
        return latest(compatible, "${project} for Minecraft ${minecraft} / Fabric")
    }

    private static List<String> mavenVersions(String url, Closure<String> readText) {
        // Preserve FileNotFoundException for the deliberate Parchment-only 404 fallback.
        String text = readText.call(url)
        try {
            def factory = DocumentBuilderFactory.newInstance()
            factory.setNamespaceAware(false)
            factory.setXIncludeAware(false)
            factory.setExpandEntityReferences(false)
            factory.setFeature(XMLConstants.FEATURE_SECURE_PROCESSING, true)
            factory.setFeature('http://apache.org/xml/features/disallow-doctype-decl', true)
            factory.setFeature('http://xml.org/sax/features/external-general-entities', false)
            factory.setFeature('http://xml.org/sax/features/external-parameter-entities', false)
            factory.setFeature('http://apache.org/xml/features/nonvalidating/load-external-dtd', false)
            factory.setAttribute(XMLConstants.ACCESS_EXTERNAL_DTD, '')
            factory.setAttribute(XMLConstants.ACCESS_EXTERNAL_SCHEMA, '')
            Element root = factory.newDocumentBuilder()
                    .parse(new InputSource(new StringReader(text))).documentElement
            if (root.tagName != 'metadata') {
                throw new IllegalArgumentException('Expected Maven metadata XML')
            }
            Element versioning = child(root, 'versioning')
            Element versions = child(versioning, 'versions')
            List<String> result = []
            def nodes = versions.childNodes
            for (int index = 0; index < nodes.length; index++) {
                def node = nodes.item(index)
                if (node instanceof Element && node.tagName == 'version') {
                    String version = node.textContent.trim()
                    // Forge and NeoForm prefix releases with the Minecraft version.
                    // The final dependency selection applies the stricter stable-release filter.
                    if (isMavenRelease(version)) {
                        result.add(version)
                    }
                }
            }
            return result.unique()
        } catch (Exception error) {
            throw new IllegalStateException("Invalid Maven version metadata from ${url}", error)
        }
    }

    private static Element child(Element parent, String name) {
        def nodes = parent.childNodes
        for (int index = 0; index < nodes.length; index++) {
            def node = nodes.item(index)
            if (node instanceof Element && node.tagName == name) {
                return (Element) node
            }
        }
        throw new IllegalArgumentException("Missing Maven metadata element: ${name}")
    }

    private static String required(Properties properties, String key) {
        String value = properties.getProperty(key)?.trim()
        if (!value) {
            throw new IllegalArgumentException("Missing property in gradle.properties: ${key}")
        }
        return value
    }

    private static boolean isStable(String version) {
        // Numeric release segments and optional SemVer build metadata. Even numeric prerelease
        // identifiers after a hyphen are excluded, alongside alpha/beta/RC and snapshots.
        return version != null && version ==~ /\d+(?:\.\d+)*(?:\+[0-9A-Za-z][0-9A-Za-z.\-]*)?/
    }

    private static boolean isMavenRelease(String version) {
        return version != null && version ==~ /\d+(?:\.\d+)*(?:-\d+(?:\.\d+)*)?(?:\+[0-9A-Za-z][0-9A-Za-z.\-]*)?/
    }

    private static String latest(Collection<String> versions, String dependency) {
        List<String> stable = versions.findAll { isStable(it) }
        if (stable.isEmpty()) {
            throw new IllegalStateException("No compatible stable release found: ${dependency}")
        }
        return stable.max { String first, String second -> compareVersions(first, second) }
    }

    private static int compareVersions(String first, String second) {
        List<BigInteger> left = numericParts(first)
        List<BigInteger> right = numericParts(second)
        int size = Math.max(left.size(), right.size())
        for (int index = 0; index < size; index++) {
            BigInteger a = index < left.size() ? left[index] : BigInteger.ZERO
            BigInteger b = index < right.size() ? right[index] : BigInteger.ZERO
            int result = a.compareTo(b)
            if (result != 0) {
                return result
            }
        }
        return first <=> second
    }

    private static List<BigInteger> numericParts(String version) {
        return version.split(/\+/, 2)[0].split(/[.\-]/).collect { new BigInteger(it) }
    }
}
