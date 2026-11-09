package com.example.order;

import javax.persistence.*;

@Entity
@Table(name = "orders")
public class OrderEntity {
    @Id
    private long id;
    private long customerId;
}
