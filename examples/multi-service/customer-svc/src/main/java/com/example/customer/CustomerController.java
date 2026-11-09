package com.example.customer;

import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/customers")
public class CustomerController {

    @GetMapping("/{id}")
    public String get(@PathVariable long id) {
        return "customer " + id;
    }

    @GetMapping("")
    public String list() {
        return "all";
    }
}
