package com.example.customer;

import javax.persistence.*;

@Entity
@Table(name = "customers")
public class Customer {
    @Id
    private long id;
    private String name;
}
