package me.n4th4not.gradle

/** Decides whether this invocation needs fresh versions before project configuration. */
final class AutoModVersionUpdates {
    private static final Set<String> MANUAL = ['checkModUpdates', 'updateModVersions'] as Set
    private static final Set<String> INFORMATIONAL = [
            'help', 'tasks', 'projects', 'properties', 'dependencies', 'dependencyInsight',
            'outgoingVariants', 'resolvableConfigurations', 'buildEnvironment', 'javaToolchains',
            'components', 'model', 'wrapper', 'clean'
    ] as Set

    static boolean shouldUpdate(String flag, Collection<String> requestedTasks) {
        if (!(flag in ['true', 'false'])) {
            throw new IllegalArgumentException('autoUpdateModVersions must be true or false.')
        }
        def names = requestedTasks.collect { it.tokenize(':').last() }
        boolean construction = names.any { !(it in INFORMATIONAL) && !(it in MANUAL) }
        if (construction && names.any { it in MANUAL }) {
            throw new IllegalArgumentException('Run version-update tasks separately from builds, or use -PautoUpdateModVersions=true.')
        }
        return flag.toBoolean() && construction
    }
}
