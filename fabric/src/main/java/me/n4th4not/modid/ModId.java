package me.n4th4not.modid;

import me.shedaniel.autoconfig.AutoConfig;
import me.shedaniel.autoconfig.serializer.GsonConfigSerializer;
import net.fabricmc.api.ModInitializer;

public class ModId
    implements ModInitializer {

    private static FabricModIdConfig CONFIG;
    
    @Override
    public void onInitialize() {
        
        // This method is invoked by the Fabric mod loader when it is ready
        // to load your mod. You can access Fabric and Common code in this
        // project.

        // Use Fabric to bootstrap the Common mod.
        Constants.LOG.info("Hello Fabric world!");
        CommonClass.init();

        //Register config and use json serializer/deserializer
        AutoConfig.register(CONFIG.getClass(), GsonConfigSerializer::new);
    }

    public static FabricModIdConfig getConfig() {
        if (CONFIG == null) return CONFIG = AutoConfig.getConfigHolder(FabricModIdConfig.class).getConfig();
        return CONFIG;
    }
}
