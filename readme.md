1. มีค่า customer_id ซ้ำกันในตาราง vw_raw_customers
2. ในตาราง vw_raw_customers มีค่าว่างในคอลัม email หรือ phone
3. ในตาราง vw_raw_customers ในคอลัม phone มีการใส่ค่าอื่นๆ เช่น +, -, (), ตัวอักษร
4. ในตาราง vw_raw_orders ในคอลัม total_amount มีค่า 0 หรือ ติดลบ
5. ในตาราง vw_raw_orders มีค่าว่างในคอลัม currency หรือ order_date