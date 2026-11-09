package com.example.legacy.repo;

import com.example.legacy.model.OrderEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;

import java.util.List;

public interface OrderRepository extends JpaRepository<OrderEntity, Long> {

    List<OrderEntity> findByCustomerId(Long customerId);

    int countByCustomerIdAndStatus(Long customerId, String status);

    /** Native SQL written by hand years ago; the report depends on it and nobody dares touch it. */
    @Query(value = "select c.id as id, c.name as name, sum(o.total) as spent, count(o.id) as orders "
                 + "from customers c join orders o on o.customerId = c.id "
                 + "group by c.id, c.name order by spent desc limit ?1", nativeQuery = true)
    List<Object[]> topCustomers(int limit);

    /** Table nobody calls any more — found by the inventory step, removed by the revival. */
    @Query(value = "select count(*) from legacy_audit", nativeQuery = true)
    long auditRowCount();
}
