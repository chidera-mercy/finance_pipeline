"""
Ingests Nigeria's annual deposit interest rate from the World Bank API.
Indicator FR.INR.DPST - deposit interest rate (%). the rate commercial
banks pay on savings/time/demand deposits. No API key required.
"""
import os

from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import execute_values
import requests

load_dotenv()

WORLDBANK_BASE_URL = "https://api.worldbank.org/v2"
INDICATOR = "FR.INR.DPST"
RATE_TYPE = "deposit"
REQUEST_TIMEOUT = 10

def get_db_connection():
    """
    Open a connection to the PostgreSQL database.
    """
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )

def fetch_interest_rates(country: str) -> list[tuple]:
    """
    Fetch the 20 most recent annual deposit interest rates for a country.
    """
    url = f"{WORLDBANK_BASE_URL}/country/{country}/indicator/{INDICATOR}"
    params = {
        "format": "json",
        "mrv": 20,
        "per_page": 20
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        records = data[1]
        return [
            (r["country"]["id"], int(r["date"]), RATE_TYPE, r["value"])
            for r in records
        ]
    except requests.exceptions.RequestException as e:
        print (f" Error fetching inflation data for {country}: {e}")
        raise

def upsert_interest_rates(conn, rows: list[tuple]) -> None:
    """
    Bulk insert/update interest rate rows.
    """
    if not rows:
        return
    try:
        with conn.cursor() as cur:
            execute_values(
                cur, 
                """
                INSERT INTO raw.interest_rates
                    (country, year, rate_type, rate_pct)
                VALUES %s
                ON CONFLICT (country, year, rate_type)
                DO UPDATE SET rate_pct = EXCLUDED.rate_pct, loaded_at = NOW()
                """, 
                rows
            )
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"  DB error while inserting interst rate rows: {e}")
        raise

def run() -> None:
    """
    Fetch and insert interest rate records into database.
    """
    conn = get_db_connection()
    try:
        country = "NG"
        rows = fetch_interest_rates(country)
        upsert_interest_rates(conn, rows)
        print(f"  Upserted {len(rows)} interest rate records for {country}")
    finally:
        conn.close()

if __name__ == "__main__":
    run()
