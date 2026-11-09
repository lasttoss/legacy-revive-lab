package com.example.legacy;

import brave.handler.MutableSpan;
import brave.handler.SpanHandler;
import brave.propagation.TraceContext;
import org.springframework.stereotype.Component;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardOpenOption;

/**
 * Writes one line per span to samples/spans.log while the tests run.
 *
 * This is the honest direction of evidence: the test executes, the trace is recorded, and the service map
 * is regenerated from what actually happened. A map drawn from a whiteboard cannot be checked; this one can.
 *
 * Test scope only: nothing here is on the production classpath.
 */
@Component
public class SpanRecorder extends SpanHandler {

    static final Path OUT = Paths.get(System.getProperty("span.out", "../samples/spans.log"));

    @Override
    public boolean end(TraceContext context, MutableSpan span, Cause cause) {
        if (context == null) {
            return true;
        }
        String line = new StringBuilder(256)
                .append("{\"trace\":\"").append(context.traceIdString()).append('"')
                .append(",\"span\":\"").append(context.spanIdString()).append('"')
                .append(",\"parent\":\"").append(context.parentIdString() == null ? "" : context.parentIdString()).append('"')
                .append(",\"name\":\"").append(esc(span.name())).append('"')
                .append(",\"method\":\"").append(esc(tag(span, "http.method"))).append('"')
                .append(",\"path\":\"").append(esc(tag(span, "http.path"))).append('"')
                .append(",\"status\":\"").append(esc(status(span))).append('"')
                // Brave timestamps are microseconds, so the field says so instead of pretending to be ms
                .append(",\"duration_us\":").append(span.finishTimestamp() - span.startTimestamp())
                .append('}').toString();
        write(line);
        return true;
    }

    private static String status(MutableSpan span) {
        String v = span.tag("http.status_code");
        if (v == null) {
            v = span.tag("otel.status_code");
        }
        return v == null ? "" : v;
    }

    private static String tag(MutableSpan span, String key) {
        String v = span.tag(key);
        return v == null ? "" : v;
    }

    private static String esc(String s) {
        return s == null ? "" : s.replace("\\", "\\\\").replace("\"", "\\\"");
    }

    private static boolean truncated;

    private static synchronized void write(String line) {
        try {
            Path p = OUT.toAbsolutePath().normalize();
            Files.createDirectories(p.getParent());
            // the first span of a run starts a fresh file: a test run must not inherit yesterday's traces
            Files.write(p, (line + System.lineSeparator()).getBytes(StandardCharsets.UTF_8),
                    StandardOpenOption.CREATE, truncated ? StandardOpenOption.APPEND : StandardOpenOption.TRUNCATE_EXISTING,
                    StandardOpenOption.WRITE);
            truncated = true;
        } catch (IOException e) {
            throw new UncheckedIOException(e);
        }
    }
}
