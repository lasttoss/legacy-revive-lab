package com.example.legacy;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.autoconfigure.domain.EntityScan;
import org.springframework.data.jpa.repository.config.EnableJpaRepositories;

/** No @ComponentScan tuning, no profiles, no global exception handler. This is the legacy shape. */
@SpringBootApplication
@EntityScan("com.example.legacy.model")
@EnableJpaRepositories("com.example.legacy.repo")
public class LegacyApplication {
    public static void main(String[] args) {
        SpringApplication.run(LegacyApplication.class, args);
    }
}
