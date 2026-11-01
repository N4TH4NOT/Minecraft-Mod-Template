package me.n4th4not.modid;

import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.terraformersmc.modmenu.api.ModMenuApi;
import net.fabricmc.api.ModInitializer;
import org.junit.jupiter.api.Test;

import java.io.IOException;
import java.lang.reflect.Modifier;
import java.nio.charset.StandardCharsets;

import static org.junit.jupiter.api.Assertions.*;

class FabricMetadataTest {

    @Test
    void generatedMetadataPointsToUsableMainEntrypoints() throws Exception {
        JsonObject metadata = JsonParser.parseString(resource("fabric.mod.json")).getAsJsonObject();
        assertEquals(System.getProperty("template.minecraft.version"),
                metadata.getAsJsonObject("depends").get("minecraft").getAsString());

        var entrypoints = metadata.getAsJsonObject("entrypoints").getAsJsonArray("main");
        assertFalse(entrypoints.isEmpty(), "A main entrypoint is required");
        for (JsonElement entrypoint : entrypoints) {
            Class<?> type = Class.forName(entrypoint.getAsString(), false, getClass().getClassLoader());
            assertTrue(ModInitializer.class.isAssignableFrom(type), entrypoint.getAsString());
            assertTrue(Modifier.isPublic(type.getModifiers()), "Fabric must be able to access its entrypoint");
            assertNotNull(type.getConstructor(), "Fabric must be able to construct its entrypoint");
        }
    }

    @Test
    void declaredModMenuEntrypointsCanBeConstructed() throws Exception {
        JsonObject metadata = JsonParser.parseString(resource("fabric.mod.json")).getAsJsonObject();
        var entrypoints = metadata.getAsJsonObject("entrypoints").getAsJsonArray("modmenu");
        assertFalse(entrypoints.isEmpty(), "The configuration screen integration must be declared");
        for (JsonElement entrypoint : entrypoints) {
            Class<?> type = Class.forName(entrypoint.getAsString(), false, getClass().getClassLoader());
            assertInstanceOf(ModMenuApi.class, type.getConstructor().newInstance());
        }
    }

    @Test
    void declaredMixinConfigurationsAndClassesArePackaged() throws IOException {
        JsonObject metadata = JsonParser.parseString(resource("fabric.mod.json")).getAsJsonObject();
        for (JsonElement name : metadata.getAsJsonArray("mixins")) {
            JsonObject mixins = JsonParser.parseString(resource(name.getAsString())).getAsJsonObject();
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
