create table if not exists legacy_audit (id integer primary key, note text);
create table if not exists legacy_flags (id integer primary key, flag text);   -- nobody queries this any more
insert into legacy_audit (id, note) values (1, 'boot');

insert into customers (id, name, email, tier) values (1, 'Alice', 'alice@example.com', 'GOLD');
insert into customers (id, name, email, tier) values (2, 'Bob', 'bob@example.com', 'SILVER');
insert into customers (id, name, email, tier) values (3, 'Carol', 'carol@example.com', null);

insert into orders (id, customerId, status, total, fee, createdAt) values (1001, 1, 'PAID', 250.00, 17.50, '2024-01-05T10:00:00');
insert into orders (id, customerId, status, total, fee, createdAt) values (1002, 1, 'OPEN', 40.00, 0.00, '2024-02-06T11:30:00');
insert into orders (id, customerId, status, total, fee, createdAt) values (1003, 2, 'CANCELLED', 900.00, 63.00, '2024-02-07T09:15:00');

insert into order_items (sku, qty, price, orderId) values ('SKU-A', 2, 100.00, 1001);
insert into order_items (sku, qty, price, orderId) values ('SKU-B', 1, 50.00, 1001);
insert into order_items (sku, qty, price, orderId) values ('SKU-C', 4, 10.00, 1002);
insert into order_items (sku, qty, price, orderId) values ('SKU-D', 3, 300.00, 1003);
