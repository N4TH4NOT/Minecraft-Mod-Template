package __MAIN_PACKAGE__;

import net.minestom.server.Auth;
import net.minestom.server.MinecraftServer;
import net.minestom.server.ServerProcess;
import net.minestom.server.coordinate.Pos;
import net.minestom.server.event.player.AsyncPlayerConfigurationEvent;
import net.minestom.server.instance.InstanceContainer;
import net.minestom.server.instance.block.Block;

/**
 * Minimal standalone server entrypoint for projects created from this template.
 *
 * <p>The default is an offline development server on loopback. Before exposing a
 * derived project, choose an authentication mode appropriate for that server.
 * Minestom has one active server process per JVM and does not load vanilla mods.
 */
public final class __MAIN_CLASS__ implements AutoCloseable {
    private final ServerProcess process;
    private final InstanceContainer instance;

    private __MAIN_CLASS__(ServerProcess process, InstanceContainer instance) {
        this.process = process;
        this.instance = instance;
    }

    /**
     * Starts the template server; port zero asks the operating system for a free port.
     *
     * @param host bind address
     * @param port listening port, or zero for an ephemeral port
     * @return the running server, which must be closed by its owner
     */
    public static __MAIN_CLASS__ start(String host, int port) {
        if (host == null || host.isBlank()) {
            throw new IllegalArgumentException("The bind address must not be blank");
        }
        if (port < 0 || port > 65535) {
            throw new IllegalArgumentException("The port must be between 0 and 65535");
        }

        MinecraftServer server = MinecraftServer.init(new Auth.Offline());
        ServerProcess process = MinecraftServer.process();
        try {
            InstanceContainer instance = process.instance().createInstanceContainer();
            instance.setGenerator(unit -> unit.modifier().fillHeight(0, 40, Block.STONE));
            process.eventHandler().addListener(AsyncPlayerConfigurationEvent.class, event -> {
                event.setSpawningInstance(instance);
                event.getPlayer().setRespawnPoint(new Pos(0.5, 42, 0.5));
            });
            server.start(host, port);
            return new __MAIN_CLASS__(process, instance);
        } catch (RuntimeException | Error failure) {
            process.stop();
            throw failure;
        }
    }

    /**
     * Starts on 127.0.0.1:25565 unless a host and optional port are supplied.
     *
     * @param args optional bind host and port
     */
    public static void main(String[] args) {
        if (args.length > 2) {
            throw new IllegalArgumentException("Usage: __MAIN_CLASS__ [host] [port]");
        }
        String host = args.length > 0 ? args[0] : "127.0.0.1";
        int port = args.length > 1 ? Integer.parseInt(args[1]) : 25565;
        __MAIN_CLASS__ server = start(host, port);
        Runtime.getRuntime().addShutdownHook(new Thread(server::close, "template-shutdown"));
    }

    public int port() {
        return process.server().getPort();
    }

    public InstanceContainer instance() {
        return instance;
    }

    public boolean isRunning() {
        return process.isAlive();
    }

    @Override
    public void close() {
        process.stop();
    }
}
