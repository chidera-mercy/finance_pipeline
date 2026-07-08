"""
Ingests Nigeria's annual CPI inflation rate from the World Bank API.
Indicator FP.CPI.TOTL.ZG - inflation, consumer prices (annual %).
No API key required.
"""
import os
from datetime import date

from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import execute_values
import requests

load_dotenv()

WORLDBANK_BASE_URL = "https://api.worldbank.org/v2"
INDICATOR = "FP.CPI.TOTL.ZG"
START_YEAR = 2020
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

def fetch_inflation(country: str) -> list[tuple]:
    """
    Fetch the annual inflation rates for a country (2020 till currently available).
    """
    url = f"{WORLDBANK_BASE_URL}/country/{country}/indicator/{INDICATOR}"
    params = {
        "format": "json",
        "date": f"{START_YEAR}:{date.today().year}",
        "per_page": 100
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        records = data[1]
        return [
            (r["country"]["id"], int(r["date"]), r["value"])
            for r in records if r["value"] is not None
        ]
    except requests.exceptions.RequestException as e:
        print (f" Error fetching inflation data for {country}: {e}")
        raise

def upsert_inflation(conn, rows: list[tuple]) -> None:
    """
    Bulk insert/update inflation rows.
    """
    if not rows:
        return
    try:
        with conn.cursor() as cur:
            execute_values(
                cur, 
                """
                INSERT INTO raw.inflation
                    (country, year, inflation)
                VALUES %s
                ON CONFLICT (country, year)
                DO UPDATE SET inflation = EXCLUDED.inflation, loaded_at = NOW()
                """, 
                rows
            )
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"  DB error while inserting inflation rows: {e}")
        raise

def run() -> None:
    """
    Fetch and insert inflation records into database.
    """
    conn = get_db_connection()
    try:
        country = "NG"
        rows = fetch_inflation(country)
        upsert_inflation(conn, rows)
        print(f"  Upserted {len(rows)} inflation records for {country}")
    finally:
        conn.close()

if __name__ == "__main__":
    run()
