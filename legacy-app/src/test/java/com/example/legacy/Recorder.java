package com.example.legacy;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.client.TestRestTemplate;
import org.springframework.boot.web.server.LocalServerPort;
import org.springframework.http.*;

import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.List;

/**
 * Phase A of the revival: replay the sampled production traffic against the running app and record
 * what it actually answers. That recording is the only honest specification a legacy service has.
 *
 * Run: mvn -Dtest=Recorder test
 */
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
public class Recorder {

    @LocalServerPort
    int port;

    @Autowired
    TestRestTemplate rest;

    static final ObjectMapper M = new ObjectMapper();

    @Test
    public void recordSampledTraffic() throws Exception {
        Path access = Paths.get(System.getProperty("samples.dir", "../samples")).resolve("access.log");
        Path out = GoldenSupport.dir();
        Files.createDirectories(out);
        if (!Files.exists(access)) {
            throw new IllegalStateException("no access log at " + access.toAbsolutePath());
        }

        List<String> lines = Files.readAllLines(access, StandardCharsets.UTF_8);
        int written = 0;
        for (String line : lines) {
            if (line.trim().isEmpty()) {
                continue;
            }
            JsonNode rec = M.readTree(line);
            String id = rec.get("id").asText();
            String method = rec.get("method").asText();
            String path = rec.get("path").asText();
            JsonNode body = rec.get("body");

            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            HttpEntity<String> entity = new HttpEntity<>(body == null ? null : body.toString(), headers);

            ResponseEntity<String> resp = rest.exchange("http://localhost:" + port + path,
                    HttpMethod.valueOf(method), entity, String.class);

            ObjectNode golden = M.createObjectNode();
            golden.put("id", id);
            golden.put("method", method);
            golden.put("path", path);
            golden.set("requestBody", body);
            golden.put("status", resp.getStatusCodeValue());
            JsonNode parsed = GoldenSupport.parse(resp.getBody());
            if (parsed == null) {
                golden.put("body", resp.getBody());
            } else {
                golden.set("body", parsed);
            }
            Files.write(out.resolve(id + ".json"),
                    M.writerWithDefaultPrettyPrinter().writeValueAsString(golden).getBytes(StandardCharsets.UTF_8));
            written++;
        }
        System.out.println("[recorder] golden cases written: " + written + " -> " + out.toAbsolutePath());
    }
}
