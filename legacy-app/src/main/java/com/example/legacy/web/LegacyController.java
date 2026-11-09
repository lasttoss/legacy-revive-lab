package com.example.legacy.web;

import com.example.legacy.model.Customer;
import com.example.legacy.model.OrderEntity;
import com.example.legacy.service.LegacyService;
import org.springframework.web.bind.annotation.*;

import java.util.*;

/** Returns entities straight to the wire. No DTO, no validation, no error contract. */
@RestController
@RequestMapping("/api")
public class LegacyController {

    private final LegacyService service;

    public LegacyController(LegacyService service) {
        this.service = service;
    }

    @GetMapping("/customers/{id}")
    public Customer customer(@PathVariable Long id) {
        return service.customerWithOrders(id);
    }

    @GetMapping("/orders/{id}")
    public OrderEntity order(@PathVariable Long id) {
        return service.order(id);
    }

    @PostMapping("/orders")
    public OrderEntity create(@RequestBody Map<String, Object> body) {
        Long customerId = Long.valueOf(String.valueOf(body.get("customerId")));
        @SuppressWarnings("unchecked")
        List<Map<String, Object>> items = (List<Map<String, Object>>) body.get("items");
        return service.createOrder(customerId, items);
    }

    @GetMapping("/reports/top")
    public List<Map<String, Object>> top(@RequestParam(defaultValue = "5") int limit) {
        List<Map<String, Object>> out = new ArrayList<>();
        for (Object[] row : service.top(limit)) {
            Map<String, Object> m = new LinkedHashMap<>();
            m.put("id", row[0]);
            m.put("name", row[1]);
            m.put("spent", row[2]);
            m.put("orders", row[3]);
            out.add(m);
        }
        return out;
    }

    @GetMapping("/legacy/ping")
    public Map<String, Object> ping() {
        Map<String, Object> m = new HashMap<>();
        m.put("ok", service.ping());
        return m;
    }
}
