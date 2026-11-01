package __PACKAGE__;

/** Engine-independent entrypoint that each target can import and call directly. */
public class CommonClass {

    /**
     * Initializes shared code using facts and a lookup supplied by the target.
     *
     * @param context information from the calling platform
     */
    public static void init(PlatformContext context) {
        Constants.LOG.info("Initializing {} on {} in {}", Constants.MOD_NAME, context.name(),
                context.development() ? "development" : "production");
        if (context.isModLoaded().test(Constants.MOD_ID)) {
            Constants.LOG.info("{} is loaded", Constants.MOD_ID);
        }
    }
}
