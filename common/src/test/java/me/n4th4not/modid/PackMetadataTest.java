package me.n4th4not.modid;

import com.google.gson.JsonParser;
import org.junit.jupiter.api.Test;

import java.io.IOException;
import java.nio.charset.StandardCharsets;

import static org.junit.jupiter.api.Assertions.*;

class PackMetadataTest {

    @Test
    void generatedPackMetadataDeclaresTheMinecraft12110FormatRange() throws IOException {
        try (var input = getClass().getClassLoader().getResourceAsStream("pack.mcmeta")) {
            assertNotNull(input, "The generated resource pack metadata must be packaged");
            String text = new String(input.readAllBytes(), StandardCharsets.UTF_8);
            assertFalse(text.contains("${"), "Pack metadata must not contain unexpanded Gradle properties");
            var pack = JsonParser.parseString(text).getAsJsonObject().getAsJsonObject("pack");

            // Minecraft 1.21.10 requires min_format and max_format for resource formats above 64.
            assertTrue(pack.has("min_format"), "The minimum resource format is required");
            assertTrue(pack.has("max_format"), "The maximum resource format is required");
            assertTrue(pack.get("min_format").getAsInt() <= 69, "The resource pack must accept format 69");
            assertTrue(pack.get("max_format").getAsInt() >= 69, "The resource pack must accept format 69");
            assertEquals(69, pack.get("pack_format").getAsInt());
        }
    }
}
