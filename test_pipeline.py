import pytest
import pandas as pd
import numpy as np

from pipeline import clean_phone_number, clean_customers_data, clean_orders_data

def test_clean_phone_number_various_formats():
    """ทดสอบการแปลงเบอร์โทรในรูปแบบต่างๆ ให้เหลือเฉพาะตัวเลข"""
    assert clean_phone_number("+1 (555) 123-4567") == "15551234567"
    assert clean_phone_number("081-234-5678") == "0812345678"
    assert clean_phone_number("555.987.6543") == "5559876543"
    assert clean_phone_number("1234567890") == "1234567890"

def test_clean_customers_data():
    """
    ทดสอบ Business Rules ของ Customers:
    - Deduplicate โดยยึด signup_date ล่าสุด
    - Clean phone number
    - เติม missing email ด้วย unknown@domain.com
    """
    dummy_customers = pd.DataFrame([
        {
            "customer_id": 1,
            "name": "Alice Old",
            "email": "alice@test.com",
            "phone": "+5-555-666",
            "signup_date": "2023-01-01"
        },
        {
            "customer_id": 1,
            "name": "Alice New",
            "email": "alice@test.com",
            "phone": "(123) 456-789",
            "signup_date": "2023-06-01"
        },
        {
            "customer_id": 2,
            "name": "Bob",
            "email": None,
            "phone": "555-555",
            "signup_date": "2023-03-01"
        }
    ])

    result_df = clean_customers_data(dummy_customers)

    assert len(result_df) == 2

    cust_1 = result_df[result_df["customer_id"] == 1].iloc[0]
    assert cust_1["name"] == "Alice New"
    assert cust_1["phone"] == "123456789"

    cust_2 = result_df[result_df["customer_id"] == 2].iloc[0]
    assert cust_2["email"] == "unknown@domain.com"
    assert cust_2["phone"] == "555555"

def test_clean_orders_data_filtering_and_conversion():
    """
    ทดสอบ Business Rules ของ Orders:
    - กรอง order ที่ total_amount <= 0 ทิ้ง
    - แปลงยอดเงินตาม exchange rate
    - ถ้า currency หายหรือไม่มี rate ให้ถือเป็น USD (rate = 1.0)
    """
    dummy_orders = pd.DataFrame([
        {"order_id": 101, "customer_id": 1, "order_date": "2023-05-01", "currency": "EUR", "total_amount": 100.0},

        {"order_id": 102, "customer_id": 2, "order_date": "2023-05-01", "currency": "USD", "total_amount": 50.0},

        {"order_id": 103, "customer_id": 3, "order_date": "2023-05-01", "currency": "USD", "total_amount": 0.0},
        
        {"order_id": 104, "customer_id": 4, "order_date": "2023-05-01", "currency": "USD", "total_amount": -20.0},

        {"order_id": 105, "customer_id": 5, "order_date": "2023-05-01", "currency": "THB", "total_amount": 150.0},

        {"order_id": 106, "customer_id": 6, "order_date": "2023-05-01", "currency": None, "total_amount": 80.0},
    ])

    dummy_rates = pd.DataFrame([
        {"currency": "EUR", "date": "2023-05-01", "rate_to_usd": 1.1},
    ])

    result_df = clean_orders_data(dummy_orders, dummy_rates)

    assert len(result_df) == 4
    assert 103 not in result_df["order_id"].values
    assert 104 not in result_df["order_id"].values

    eur_order = result_df[result_df["order_id"] == 101].iloc[0]
    assert eur_order["usd_amount"] == 110.00

    usd_order = result_df[result_df["order_id"] == 102].iloc[0]
    assert usd_order["usd_amount"] == 50.00

    jpy_order = result_df[result_df["order_id"] == 105].iloc[0]
    assert jpy_order["usd_amount"] == 150.00

    null_curr_order = result_df[result_df["order_id"] == 106].iloc[0]
    assert null_curr_order["usd_amount"] == 80.00