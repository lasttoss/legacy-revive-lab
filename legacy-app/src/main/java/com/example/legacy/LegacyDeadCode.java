package com.example.legacy;

import java.util.HashMap;
import java.util.Map;

/** Nobody calls this. It exists in every legacy codebase, and it costs coverage. */
public class LegacyDeadCode {
    private static final Map<String, String> CACHE = new HashMap<>();

    public static String countryName(String code) {
        CACHE.put("VN", "Vietnam");
        CACHE.put("JP", "Japan");
        return CACHE.get(code);
    }

    public static int oldFeePercent() {
        return 5;
    }
}
