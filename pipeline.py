import os
import re
import sqlite3
import pandas as pd
from prefect import flow, task, get_run_logger

SOURCE_DB_PATH = "shopdata.db"
TARGET_DB_PATH = "analytics.db"

def clean_phone_number(phone_val) -> str:
    """
    จัดรูปแบบเบอร์โทรศัพท์ให้เหลือเฉพาะตัวเลข 0-9
    เช่น '+1 (555) 123-4567' -> '15551234567'
    """
    if pd.isna(phone_val):
        return ""
    return re.sub(r"[^0-9]", "", str(phone_val))


def clean_customers_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Business Rules สำหรับ Customers:
    1. Deduplicate records โดยยึด signup_date ล่าสุดเป็นหลัก
    2. จัดรูปแบบ phone ให้เหลือเฉพาะตัวเลข
    3. แทนที่ missing email ด้วย 'unknown@domain.com'
    """
    df = df.copy()

    df["signup_date_dt"] = pd.to_datetime(df["signup_date"], errors="coerce")
    
    df = df.sort_values(by=["customer_id", "signup_date_dt"], ascending=[True, False])
    
    df = df.drop_duplicates(subset=["customer_id"], keep="first")
    df = df.drop(columns=["signup_date_dt"])

    df["phone"] = df["phone"].apply(clean_phone_number)

    df["email"] = df["email"].fillna("unknown@domain.com")
    df.loc[df["email"].astype(str).str.strip() == "", "email"] = "unknown@domain.com"

    return df


def clean_orders_data(orders_df: pd.DataFrame, rates_df: pd.DataFrame) -> pd.DataFrame:
    """
    Business Rules สำหรับ Orders:
    1. กรอง order ที่มี total_amount <= 0 ทิ้ง
    2. แปลงยอดเงินเป็น USD (usd_amount) โดยเทียบวันที่กับ vw_exchange_rates
       หากสกุลเงินหายไป หรือหาเรทไม่เจอ ให้ถือว่าเป็น USD (เรท = 1.0)
    """
    df = orders_df.copy()

    df = df[df["total_amount"] > 0].copy()

    df["currency"] = df["currency"].fillna("USD")
    df.loc[df["currency"].astype(str).str.strip() == "", "currency"] = "USD"

    rates = rates_df.copy()
    rates = rates.rename(columns={"date": "order_date"})

    merged = pd.merge(
        df,
        rates[["currency", "order_date", "rate_to_usd"]],
        on=["currency", "order_date"],
        how="left"
    )

    merged["rate_to_usd"] = merged["rate_to_usd"].fillna(1.0)
    merged.loc[merged["currency"] == "USD", "rate_to_usd"] = 1.0

    merged["usd_amount"] = (merged["total_amount"] * merged["rate_to_usd"]).round(2)

    clean_orders = merged.drop(columns=["rate_to_usd"])

    return clean_orders

@task(retries=2, retry_delay_seconds=5)
def extract_data(source_db: str):
    """อ่านข้อมูลจาก SQLite views"""
    logger = get_run_logger()
    logger.info(f"Extracting raw data from {source_db}")
    
    if not os.path.exists(source_db):
        raise FileNotFoundError(f"Database file not found: {source_db}")

    with sqlite3.connect(source_db) as conn:
        customers_df = pd.read_sql_query("SELECT * FROM vw_raw_customers", conn)
        orders_df = pd.read_sql_query("SELECT * FROM vw_raw_orders", conn)
        rates_df = pd.read_sql_query("SELECT * FROM vw_exchange_rates", conn)

    logger.info(f"Extracted: {len(customers_df)} customers, {len(orders_df)} orders, {len(rates_df)} rates")
    return customers_df, orders_df, rates_df


@task
def transform_data(customers_df: pd.DataFrame, orders_df: pd.DataFrame, rates_df: pd.DataFrame):
    """ประมวลผลและทำความสะอาดข้อมูลตาม Business Rules"""
    logger = get_run_logger()
    logger.info("Transforming customers and orders data...")

    clean_cust = clean_customers_data(customers_df)
    clean_ord = clean_orders_data(orders_df, rates_df)

    logger.info(f"Transformed: {len(clean_cust)} clean customers, {len(clean_ord)} valid orders")
    return clean_cust, clean_ord


@task
def load_data(customers_df: pd.DataFrame, orders_df: pd.DataFrame, target_db: str):
    """บันทึกข้อมูลที่คลีนแล้วลงใน analytics.db (พร้อม fallback เป็น CSV)"""
    logger = get_run_logger()
    logger.info(f"Loading data into {target_db}...")

    try:
        with sqlite3.connect(target_db) as conn:
            customers_df.to_sql("dim_customers", conn, if_exists="replace", index=False)
            orders_df.to_sql("fct_orders", conn, if_exists="replace", index=False)
        logger.info(f"Successfully loaded data into {target_db} (dim_customers, fct_orders)")
    except Exception as e:
        logger.warning(f"Failed to write to SQLite ({e}). Falling back to CSV export...")
        customers_df.to_csv("clean_customers.csv", index=False)
        orders_df.to_csv("clean_orders.csv", index=False)
        logger.info("Saved fallback CSV files: clean_customers.csv, clean_orders.csv")

@flow(name="shopdata_etl_pipeline")
def run_pipeline():
    logger = get_run_logger()
    logger.info("Starting ShopData ETL Pipeline...")
    
    # 1. Extract
    cust_raw, orders_raw, rates_raw = extract_data(SOURCE_DB_PATH)
    
    # 2. Transform
    cust_clean, orders_clean = transform_data(cust_raw, orders_raw, rates_raw)
    
    # 3. Load
    load_data(cust_clean, orders_clean, TARGET_DB_PATH)
    
    logger.info("Pipeline completed successfully!")


if __name__ == "__main__":
    run_pipeline()