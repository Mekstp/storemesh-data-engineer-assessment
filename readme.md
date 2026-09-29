Data Exploration Findings
1. มีค่า customer_id ซ้ำกันในตาราง vw_raw_customers
2. ในตาราง vw_raw_customers มีค่าว่างในคอลัม email หรือ phone
3. ในตาราง vw_raw_customers ในคอลัม phone มีการใส่ค่าอื่นๆ เช่น +, -, (), ตัวอักษร
4. ในตาราง vw_raw_orders ในคอลัม total_amount มีค่า 0 หรือ ติดลบ
5. ในตาราง vw_raw_orders มีค่าว่างในคอลัม currency หรือ order_date
6. ในตาราง vw_raw_orders มีค่าในคอลัม customer_id ที่ไม่อยู่ในตาราง vw_raw_customers

ขั้นตอนการ run project

1. ทำการ Clone repository:
git clone 
cd data-engineer-assessment

2. สร้างและเปิดใช้งาน Virtual Environment:
macOS / Linux:
python3.12 -m venv venv
source venv/bin/activate
Windows (PowerShell):
python -m venv venv
.\venv\Scripts\Activate.ps1

3. ติดตั้งแพ็กเกจที่จำเป็น:
pip install -r requirements.txt

4. รัน ETL Pipeline:
python pipeline.py

5. รัน Unit Tests:
pytest
