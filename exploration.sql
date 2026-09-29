SELECT customer_id, COUNT(*) AS count
FROM vw_raw_customers
GROUP BY customer_id
HAVING COUNT(*) > 1;

SELECT customer_id, email, phone
FROM vw_raw_customers
WHERE email IS NULL 
OR phone IS NULL 
OR phone LIKE '%+%' 
OR phone LIKE '%-%' 
OR phone LIKE '%(%' 
OR phone GLOB '*[^0-9]*';

SELECT *
FROM vw_raw_orders
WHERE total_amount <= 0;

SELECT *
FROM vw_raw_orders
WHERE currency IS NULL 
OR order_date IS NULL 
OR total_amount IS NULL;

SELECT DISTINCT o.customer_id
FROM vw_raw_orders o
LEFT JOIN vw_raw_customers c ON o.customer_id = c.customer_id
WHERE c.customer_id IS NULL;