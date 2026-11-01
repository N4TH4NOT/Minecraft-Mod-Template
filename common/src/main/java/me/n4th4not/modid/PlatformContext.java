package me.n4th4not.modid;

import java.util.Objects;
import java.util.function.Predicate;

/**
 * Runtime information supplied explicitly by the target that calls common code.
 *
 * @param name platform name
 * @param development whether this is a development environment
 * @param isModLoaded lookup supplied by the target, without exposing its loader API
 */
public record PlatformContext(String name, boolean development, Predicate<String> isModLoaded) {
    public PlatformContext {
        Objects.requireNonNull(name, "name");
        Objects.requireNonNull(isModLoaded, "isModLoaded");
    }
}
