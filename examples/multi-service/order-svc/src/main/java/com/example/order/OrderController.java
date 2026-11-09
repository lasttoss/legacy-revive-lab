package com.example.order;

import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/orders")
public class OrderController {

    @GetMapping("/{id}")
    public String get(@PathVariable long id) {
        return "order " + id;
    }

    @PostMapping("")
    public String create() {
        return "created";
    }
}
