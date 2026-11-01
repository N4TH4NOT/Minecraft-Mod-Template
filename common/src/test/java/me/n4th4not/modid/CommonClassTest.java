package me.n4th4not.modid;

import org.junit.jupiter.api.Test;

import java.util.ArrayList;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;

class CommonClassTest {

    @Test
    void sharedInitializationDelegatesTheModLookupToTheCallingTarget() {
        List<String> requestedIds = new ArrayList<>();
        PlatformContext context = new PlatformContext("Test platform", true, modId -> {
            requestedIds.add(modId);
            return true;
        });

        CommonClass.init(context);

        assertEquals(List.of(Constants.MOD_ID), requestedIds,
                "Common code must use the target callback for its own mod identifier");
    }

    @Test
    void identityMatchesTheCentralConfiguration() {
        assertEquals(System.getProperty("template.mod.id"), Constants.MOD_ID,
                "Constants.MOD_ID must match mod_id in gradle.properties");
        assertEquals(System.getProperty("template.mod.name"), Constants.MOD_NAME,
                "Constants.MOD_NAME must match mod_name in gradle.properties");
    }

    @Test
    void contextRequiresAPlatformNameAndModLookup() {
        assertThrows(NullPointerException.class, () -> new PlatformContext(null, false, ignored -> false));
        assertThrows(NullPointerException.class, () -> new PlatformContext("Test platform", false, null));
    }
}
