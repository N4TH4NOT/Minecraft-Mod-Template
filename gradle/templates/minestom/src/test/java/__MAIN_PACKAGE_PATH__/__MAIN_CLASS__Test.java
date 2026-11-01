package __MAIN_PACKAGE__;

import com.google.gson.JsonParser;
import __PACKAGE__.Constants;
import net.minestom.server.MinecraftServer;
import net.minestom.server.instance.block.Block;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.Timeout;

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.DataInputStream;
import java.io.DataOutputStream;
import java.io.IOException;
import java.net.InetSocketAddress;
import java.net.Socket;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.TimeUnit;

import static org.junit.jupiter.api.Assertions.*;

class __MAIN_CLASS__Test {

    @Test
    @Timeout(value = 30, threadMode = Timeout.ThreadMode.SEPARATE_THREAD)
    void emptyTemplateGeneratesAWorldServesMinecraftStatusAndStops() throws Exception {
        __MAIN_CLASS__ server = __MAIN_CLASS__.start("127.0.0.1", 0, true);
        try (server) {
            assertTrue(server.isRunning(), "The real Minestom process must start");
            assertTrue(server.port() > 0, "The operating system must allocate a listening port");
            assertEquals("Minestom", server.platformContext().name());
            assertTrue(server.platformContext().development(), "The explicit development flag must reach shared code");
            assertFalse(server.platformContext().isModLoaded().test(Constants.MOD_ID), "Minestom does not load this mod");
            assertFalse(server.platformContext().isModLoaded().test("unknown_mod"), "Minestom does not load external mods");

            server.instance().loadChunk(0, 0).get(10, TimeUnit.SECONDS);
            assertEquals(Block.STONE, server.instance().getBlock(0, 39, 0));
            assertEquals(Block.AIR, server.instance().getBlock(0, 40, 0));

            try (Socket socket = new Socket()) {
                socket.connect(new InetSocketAddress("127.0.0.1", server.port()), 5_000);
                socket.setSoTimeout(5_000);
                DataOutputStream output = new DataOutputStream(socket.getOutputStream());
                DataInputStream input = new DataInputStream(socket.getInputStream());

                sendHandshake(output, server.port());
                sendPacket(output, new byte[]{0}); // Status request, packet ID 0.

                try (DataInputStream response = readPacket(input)) {
                    assertEquals(0, readVarInt(response), "Expected a Minecraft status response");
                    int jsonLength = readVarInt(response);
                    assertTrue(jsonLength > 0 && jsonLength <= response.available());
                    String json = new String(response.readNBytes(jsonLength), StandardCharsets.UTF_8);
                    assertEquals(0, response.available(), "No unexpected bytes in the status response");
                    var version = JsonParser.parseString(json).getAsJsonObject().getAsJsonObject("version");
                    assertEquals(System.getProperty("template.minecraft.version"), version.get("name").getAsString());
                    assertEquals(MinecraftServer.PROTOCOL_VERSION, version.get("protocol").getAsInt());
                }

                long nonce = 0x123456789ABCDEFL;
                ByteArrayOutputStream pingBytes = new ByteArrayOutputStream();
                DataOutputStream ping = new DataOutputStream(pingBytes);
                writeVarInt(ping, 1);
                ping.writeLong(nonce);
                sendPacket(output, pingBytes.toByteArray());
                try (DataInputStream pong = readPacket(input)) {
                    assertEquals(1, readVarInt(pong), "Expected a Minecraft pong response");
                    assertEquals(nonce, pong.readLong(), "The server must return the ping payload");
                    assertEquals(0, pong.available());
                }
            }
        }
        assertFalse(server.isRunning(), "Closing the template must stop Minestom");
    }

    private static void sendHandshake(DataOutputStream output, int port) throws IOException {
        ByteArrayOutputStream bytes = new ByteArrayOutputStream();
        DataOutputStream handshake = new DataOutputStream(bytes);
        writeVarInt(handshake, 0);
        writeVarInt(handshake, MinecraftServer.PROTOCOL_VERSION);
        byte[] host = "127.0.0.1".getBytes(StandardCharsets.UTF_8);
        writeVarInt(handshake, host.length);
        handshake.write(host);
        handshake.writeShort(port);
        writeVarInt(handshake, 1); // Enter the status connection state.
        sendPacket(output, bytes.toByteArray());
    }

    private static void sendPacket(DataOutputStream output, byte[] packet) throws IOException {
        writeVarInt(output, packet.length);
        output.write(packet);
        output.flush();
    }

    private static DataInputStream readPacket(DataInputStream input) throws IOException {
        int length = readVarInt(input);
        assertTrue(length > 0 && length <= 1_048_576, "Invalid Minecraft packet length");
        byte[] packet = input.readNBytes(length);
        assertEquals(length, packet.length, "The server must send a complete packet");
        return new DataInputStream(new ByteArrayInputStream(packet));
    }

    private static void writeVarInt(DataOutputStream output, int value) throws IOException {
        while ((value & ~0x7F) != 0) {
            output.writeByte((value & 0x7F) | 0x80);
            value >>>= 7;
        }
        output.writeByte(value);
    }

    private static int readVarInt(DataInputStream input) throws IOException {
        int value = 0;
        for (int shift = 0; shift < 35; shift += 7) {
            int next = input.readUnsignedByte();
            value |= (next & 0x7F) << shift;
            if ((next & 0x80) == 0) {
                return value;
            }
        }
        throw new IOException("Minecraft VarInt exceeds five bytes");
    }
}
