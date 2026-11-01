package me.n4th4not.modid;

import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import net.minecraftforge.fml.common.Mod;
import org.junit.jupiter.api.Test;
import org.tomlj.Toml;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.stream.IntStream;

import static org.junit.jupiter.api.Assertions.*;

class ForgeMetadataTest {

    @Test
    void generatedDescriptorMatchesModEntrypointAndMinecraftVersion() throws IOException {
        var descriptor = Toml.parse(resource("META-INF/mods.toml"));
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
        assertEquals(Boolean.TRUE, minecraft.getBoolean("mandatory"));
    }

    @Test
    void sharedAndForgeMixinConfigurationsAndClassesArePackaged() throws IOException {
        var descriptor = Toml.parse(resource("META-INF/mods.toml"));
        assertFalse(descriptor.hasErrors(), () -> descriptor.errors().toString());
        String modId = descriptor.getArray("mods").getTable(0).getString("modId");
        for (String name : new String[]{modId + ".mixins.json", modId + ".forge.mixins.json"}) {
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

    private String resource(String name) throws IOException {
        try (var input = getClass().getClassLoader().getResourceAsStream(name)) {
            assertNotNull(input, "Missing generated resource: " + name);
            String text = new String(input.readAllBytes(), StandardCharsets.UTF_8);
            assertFalse(text.contains("${"), "Unexpanded Gradle property in " + name);
            return text;
        }
    }
}
