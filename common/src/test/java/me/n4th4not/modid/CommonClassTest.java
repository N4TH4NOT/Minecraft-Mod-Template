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
    void contextRequiresAPlatformNameAndModLookup() {
        assertThrows(NullPointerException.class, () -> new PlatformContext(null, false, ignored -> false));
        assertThrows(NullPointerException.class, () -> new PlatformContext("Test platform", false, null));
    }
}
