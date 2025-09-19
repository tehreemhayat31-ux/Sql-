CREATE TABLE customers (id INTEGER PRIMARY KEY, name TEXT);
CREATE TABLE orders (id INTEGER PRIMARY KEY, customer_id INTEGER, order_date TEXT, total REAL);
INSERT INTO customers (name) VALUES ('Alice'), ('Bob'), ('Charlie');
INSERT INTO orders (customer_id, order_date, total) VALUES
(1, '2024-01-12', 100.0),
(1, '2024-02-15', 50.0),
(2, '2024-03-01', 200.0); 