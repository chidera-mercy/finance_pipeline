"""
Ingests gold spot prices (USD per troy ounce, XAU/USD).

- load_csv_backfill(): one-time historical load from a trimmed
  Stooq CSV (https://stooq.com/q/d/l/?s=xauusd&i=d), source='stooq'
- run(): daily incremental load from GoldAPI.io's historical-close
  endpoint, source='goldapi'. Requires API key.
"""
import os
from datetime import date, timedelta

from dotenv import load_dotenv
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
import requests

load_dotenv()

GOLDAPI_BASE_URL = "https://www.goldapi.io/api/XAU/USD"
GOLD_API_KEY = os.getenv("GOLD_API_KEY")
REQUEST_TIMEOUT = 10

def get_db_connection():
    """
    Open a  connection to the PostgreSQL database
    """
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )

def upsert_gold_bulk(conn, rows: list[tuple]) -> None:
    """
    Bulk insert/update gold price rows.
    Each row: (price_date, close_usd, source).
    """
    if not rows:
        return
    try:
        with conn.cursor() as cur:
            execute_values(
                cur,
                """
                INSERT INTO raw.gold_prices
                    (price_date, close_usd, source)
                VALUES %s
                ON CONFLICT (price_date)
                DO UPDATE SET close_usd = EXCLUDED.close_usd, 
                              source = EXCLUDED.source,
                              loaded_at = NOW()
                """,
                rows
            )
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"  DB error while inserting gold price rows: {e}")
        raise

def load_csv_backfill(filepath: str = "data/gold_prices_2020_2026.csv") -> None:
    """
    One-time historical load from a Stooq CSV.
    Expects columns 'Date' and 'Close'.
    """
    df = pd.read_csv(filepath, parse_dates=["Date"])
    df = df.rename(columns={"Date": "price_date", "Close": "close_usd"})
    df = df[["price_date", "close_usd"]].dropna()

    rows = [
        (row.price_date.date(), float(row.close_usd), "stooq")
        for row in df.itertuples(index=False)
    ]

    conn = get_db_connection()
    try:
        upsert_gold_bulk(conn, rows)
        print(f" Backflled {len(rows)} gold price rows from Stooq CSV")
    finally:
        conn.close()

def fetch_historical_close(for_date: date) -> float:
    """
    Fetch the historical close price for a given date from GoldAPI.io.
    GET /XAU/USD/YYYYMMDD with header x-access-token.
    """
    url = f"{GOLDAPI_BASE_URL}/{for_date.strftime('%Y%m%d')}"
    headers = {"x-access-token": GOLD_API_KEY}
    try:
        response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        data = response.json()
        return data["price"]
    except requests.exceptions.RequestException as e:
        print(f"  Error fetching gold price for {for_date}: {e}")
        raise

def run(days_back: int = 1) -> None:
    """
    Daily incremental run. Fetches and stores yesterday's gold close price.
    """
    target_date = date.today() - timedelta(days=days_back)
    close_price = fetch_historical_close(target_date)

    conn = get_db_connection()
    try:
        upsert_gold_bulk(conn, [(target_date, close_price, "goldapi")])
        print(f"  Inserted gold close price for {target_date}: ${close_price}")
    finally:
        conn.close()

if __name__ == "__main__":
    print("Loading historical gold prices from Stooq CSV")
    load_csv_backfill()
    print("Backfill complete.")
