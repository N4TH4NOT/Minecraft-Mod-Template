package __PACKAGE__;


import net.neoforged.bus.api.IEventBus;
import net.neoforged.fml.common.Mod;
import net.neoforged.fml.ModList;
import net.neoforged.fml.loading.FMLLoader;

@Mod(Constants.MOD_ID)
public class ModId {

    public ModId(IEventBus eventBus) {

        // This method is invoked by the NeoForge mod loader when it is ready
        // to load your mod. You can access NeoForge and Common code in this
        // project.

        // Use NeoForge to bootstrap the Common mod.
        Constants.LOG.info("Hello NeoForge world!");
        CommonClass.init(new PlatformContext("NeoForge", !FMLLoader.getCurrent().isProduction(),
                modId -> ModList.get().isLoaded(modId)));
    }
}
