package com.example.legacy;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.*;

/**
 * Support for golden-master replay. Hand-written on purpose: it is the harness, not the test.
 *
 * Volatile fields are masked before comparison, because they carry no contract:
 * error "timestamp", jpa ids created from the clock, and the request elapsed time.
 */
public final class GoldenSupport {

    public static final ObjectMapper M = new ObjectMapper();
    private static final Set<String> VOLATILE = new HashSet<>(Arrays.asList(
            "timestamp", "trace", "path",
            "createdAt",   // clock value: differs between recording and replay
            "id"));        // generated: order id comes from System.currentTimeMillis()        // generated: the order id comes from System.currentTimeMillis()

    private GoldenSupport() { }

    public static Path dir() {
        return Paths.get(System.getProperty("golden.dir", "../samples/golden"));
    }

    /** All recorded cases, sorted by id, so failures are stable. */
    public static List<JsonNode> all() throws IOException {
        List<JsonNode> out = new ArrayList<>();
        if (!Files.isDirectory(dir())) {
            return out;
        }
        List<Path> files = new ArrayList<>();
        Files.list(dir()).filter(p -> p.toString().endsWith(".json")).forEach(files::add);
        Collections.sort(files);
        for (Path f : files) {
            out.add(M.readTree(new String(Files.readAllBytes(f), StandardCharsets.UTF_8)));
        }
        return out;
    }

    /** Remove fields that legitimately change between runs, recursively. */
    public static JsonNode mask(JsonNode node) {
        if (node == null) {
            return null;
        }
        if (node.isObject()) {
            ObjectNode copy = node.deepCopy();
            List<String> drop = new ArrayList<>();
            Iterator<String> it = copy.fieldNames();
            while (it.hasNext()) {
                String name = it.next();
                if (VOLATILE.contains(name)) {
                    drop.add(name);
                }
            }
            for (String d : drop) {
                copy.remove(d);
            }
            Iterator<Map.Entry<String, JsonNode>> fields = copy.fields();
            List<Map.Entry<String, JsonNode>> snapshot = new ArrayList<>();
            while (fields.hasNext()) {
                snapshot.add(fields.next());
            }
            for (Map.Entry<String, JsonNode> e : snapshot) {
                copy.set(e.getKey(), mask(e.getValue()));
            }
            return copy;
        }
        if (node.isArray()) {
            com.fasterxml.jackson.databind.node.ArrayNode arr = M.createArrayNode();
            for (JsonNode child : node) {
                arr.add(mask(child));
            }
            return arr;
        }
        return node;
    }

    public static JsonNode parse(String body) {
        try {
            return M.readTree(body == null ? "" : body);
        } catch (Exception e) {
            return null;   // not JSON: compare as text
        }
    }
}
