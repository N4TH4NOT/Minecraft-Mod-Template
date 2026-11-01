package __PACKAGE__;

import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import net.neoforged.fml.common.Mod;
import org.junit.jupiter.api.Test;
import org.tomlj.Toml;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.HashSet;
import java.util.Set;
import java.util.stream.IntStream;

import static org.junit.jupiter.api.Assertions.*;

class NeoForgeMetadataTest {

    @Test
    void generatedDescriptorMatchesModEntrypointAndMinecraftVersion() throws IOException {
        var descriptor = Toml.parse(resource("META-INF/neoforge.mods.toml"));
        assertFalse(descriptor.hasErrors(), () -> descriptor.errors().toString());
        var mods = descriptor.getArray("mods");
        assertNotNull(mods);
        assertEquals(1, mods.size());
        String modId = mods.getTable(0).getString("modId");
        assertEquals(modId, ModId.class.getAnnotation(Mod.class).value(), "The loader must find the declared mod");

        var dependencies = descriptor.getArray("dependencies." + modId);
        assertNotNull(dependencies);
        var minecraft = IntStream.range(0, dependencies.size()).mapToObj(dependencies::getTable)
                .filter(dependency -> "minecraft".equals(dependency.getString("modId")))
                .findFirst().orElseThrow();
        assertEquals(System.getProperty("template.minecraft.version.range"), minecraft.getString("versionRange"));
        assertEquals("required", minecraft.getString("type"));
    }

    @Test
    void declaredMixinConfigurationsAndClassesArePackaged() throws IOException {
        var descriptor = Toml.parse(resource("META-INF/neoforge.mods.toml"));
        assertFalse(descriptor.hasErrors(), () -> descriptor.errors().toString());
        var configurations = descriptor.getArray("mixins");
        assertNotNull(configurations);
        assertFalse(configurations.isEmpty(), "Shared and loader mixin configurations must be declared");
        for (int index = 0; index < configurations.size(); index++) {
            String name = configurations.getTable(index).getString("config");
            JsonObject mixins = JsonParser.parseString(resource(name)).getAsJsonObject();
            assertEquals("JAVA_" + System.getProperty("template.java.version"),
                    mixins.get("compatibilityLevel").getAsString());
            for (String side : new String[]{"mixins", "client", "server"}) {
                for (JsonElement mixin : mixins.getAsJsonArray(side)) {
                    String className = mixins.get("package").getAsString() + "." + mixin.getAsString();
                    assertNotNull(getClass().getClassLoader().getResource(className.replace('.', '/') + ".class"), className);
                }
            }
        }
    }

    @Test
    void everyMixinClassInAConfiguredPackageIsDeclared() throws Exception {
        var descriptor = Toml.parse(resource("META-INF/neoforge.mods.toml"));
        assertFalse(descriptor.hasErrors(), () -> descriptor.errors().toString());
        var configurations = descriptor.getArray("mixins");
        assertNotNull(configurations);
        Set<String> declared = new HashSet<>();
        Set<String> packages = new HashSet<>();
        for (int index = 0; index < configurations.size(); index++) {
            String name = configurations.getTable(index).getString("config");
            JsonObject mixins = JsonParser.parseString(resource(name)).getAsJsonObject();
            String packageName = mixins.get("package").getAsString();
            packages.add(packageName);
            for (String side : new String[]{"mixins", "client", "server"}) {
                for (JsonElement mixin : mixins.getAsJsonArray(side)) {
                    declared.add(packageName + "." + mixin.getAsString());
                }
            }
        }
        for (String packageName : packages) {
            var directories = getClass().getClassLoader().getResources(packageName.replace('.', '/'));
            while (directories.hasMoreElements()) {
                var directory = directories.nextElement();
                if (!"file".equals(directory.getProtocol())) {
                    continue;
                }
                try (var files = Files.list(Path.of(directory.toURI()))) {
                    files.map(file -> file.getFileName().toString())
                            .filter(file -> file.endsWith(".class") && !file.contains("$")
                                    && !file.equals("package-info.class"))
                            .forEach(file -> {
                                String className = packageName + "." + file.substring(0, file.length() - ".class".length());
                                assertTrue(declared.contains(className), "Undeclared mixin class: " + className);
                            });
                }
            }
        }
    }

    private String resource(String name) throws IOException {
        try (var input = getClass().getClassLoader().getResourceAsStream(name)) {
            assertNotNull(input, "Missing generated resource: " + name);
            String text = new String(input.readAllBytes(), StandardCharsets.UTF_8);
            assertFalse(text.contains("${"), "Unexpanded Gradle property in " + name);
            return text;
        }
    }
}
