package com.example.gateway;

import org.springframework.web.bind.annotation.*;

/** Edge service: everything a browser calls enters here. */
@RestController
@RequestMapping("/api")
public class GatewayController {

    @GetMapping("/ping")
    public String ping() {
        return "ok";
    }

    @PostMapping("/session")
    public String session() {
        return "issued";
    }
}
