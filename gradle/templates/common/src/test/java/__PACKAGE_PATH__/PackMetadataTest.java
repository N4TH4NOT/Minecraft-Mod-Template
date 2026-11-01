package __PACKAGE__;

import com.google.gson.JsonParser;
import org.junit.jupiter.api.Test;

import java.io.IOException;
import java.nio.charset.StandardCharsets;

import static org.junit.jupiter.api.Assertions.*;

class PackMetadataTest {

    @Test
    void generatedPackMetadataDeclaresTheConfiguredFormatRange() throws IOException {
        try (var input = getClass().getClassLoader().getResourceAsStream("pack.mcmeta")) {
            assertNotNull(input, "The generated resource pack metadata must be packaged");
            String text = new String(input.readAllBytes(), StandardCharsets.UTF_8);
            assertFalse(text.contains("${"), "Pack metadata must not contain unexpanded Gradle properties");
            var pack = JsonParser.parseString(text).getAsJsonObject().getAsJsonObject("pack");

            String configuredFormat = System.getProperty("template.minecraft.pack.version");
            assertNotNull(configuredFormat, "The resource pack format must be supplied by the build");
            int expectedFormat = Integer.parseInt(configuredFormat);
            assertTrue(pack.has("min_format"), "The minimum resource format is required");
            assertTrue(pack.has("max_format"), "The maximum resource format is required");
            assertTrue(pack.get("min_format").getAsInt() <= expectedFormat,
                    "The minimum resource format must accept the configured format");
            assertTrue(pack.get("max_format").getAsInt() >= expectedFormat,
                    "The maximum resource format must accept the configured format");
            assertEquals(expectedFormat, pack.get("pack_format").getAsInt());
        }
    }
}
