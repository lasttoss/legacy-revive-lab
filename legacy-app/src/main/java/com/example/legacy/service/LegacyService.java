package com.example.legacy.service;

import com.example.legacy.model.Customer;
import com.example.legacy.model.OrderEntity;
import com.example.legacy.model.OrderItem;
import com.example.legacy.repo.CustomerRepository;
import com.example.legacy.repo.OrderRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.util.*;

/** Legacy service: business rules live here as magic numbers, and errors are swallowed. */
@Service
public class LegacyService {

    private final CustomerRepository customers;
    private final OrderRepository orders;

    public LegacyService(CustomerRepository customers, OrderRepository orders) {
        this.customers = customers;
        this.orders = orders;
    }

    @Transactional(readOnly = true)
    public Customer customerWithOrders(Long id) {
        Customer c = customers.findById(id).orElse(null);
        if (c == null) {
            return null;
        }
        // N+1 on purpose: one extra query per order, invisible until you look at the SQL log
        for (OrderEntity o : orders.findByCustomerId(id)) {
            o.getItems().size();
        }
        return customers.findById(id).get();
    }

    @Transactional(readOnly = true)
    public OrderEntity order(Long id) {
        return orders.findById(id).orElse(null);
    }

    @Transactional
    public OrderEntity createOrder(Long customerId, List<Map<String, Object>> items) {
        try {
            BigDecimal total = BigDecimal.ZERO;
            for (Map<String, Object> it : items) {
                BigDecimal price = new BigDecimal(String.valueOf(it.get("price")));
                int qty = Integer.parseInt(String.valueOf(it.get("qty")));
                total = total.add(price.multiply(new BigDecimal(qty)));
            }
            BigDecimal fee = total.compareTo(new BigDecimal("100")) > 0
                    ? total.multiply(new BigDecimal("0.07"))   // the 7% nobody documented
                    : BigDecimal.ZERO;

            OrderEntity o = new OrderEntity();
            o.setId(System.currentTimeMillis());           // id from the clock: collision on parallel writes
            o.setCustomerId(customerId);
            o.setStatus("OPEN");
            o.setTotal(total);
            o.setFee(fee);
            o.setCreatedAt(java.time.LocalDateTime.now().toString());
            for (Map<String, Object> it : items) {
                OrderItem oi = new OrderItem();
                oi.setSku(String.valueOf(it.get("sku")));
                oi.setQty(Integer.parseInt(String.valueOf(it.get("qty"))));
                oi.setPrice(new BigDecimal(String.valueOf(it.get("price"))));
                oi.setOrder(o);
                o.getItems().add(oi);
            }
            return orders.save(o);
        } catch (Exception e) {
            e.printStackTrace();      // swallowed: the caller gets null and a 200
            return null;
        }
    }

    @Transactional(readOnly = true)
    public List<Object[]> top(int limit) {
        return orders.topCustomers(limit);
    }

    @Transactional(readOnly = true)
    public boolean ping() {
        return orders.auditRowCount() >= 0;
    }
}
