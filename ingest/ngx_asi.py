"""
Ingests the NGX All-Share Index (ASI) from the NGX Pulse API.
Requires a registeres API key.
"""
import os
from datetime import date, timedelta

from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import execute_values
import requests

load_dotenv()

NGX_PULSE_BASE_URL = "http://www.ngxpulse.ng"
NGX_PULSE_API_KEY = os.getenv("NGX_PULSE_API_KEY")
REQUEST_TIMEOUT = 15

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

def fetch_asi_history(start_date: date, end_date: date) -> list[dict]:
    """
    Fetch ASI values for a date range.
    GET /api/ngxdata/indices/asi/history?from=YYYY-MM-DD&to=YYYY-MM-DD
    Returns a list of {"date": "YYYY-MM-DD", "value": float}.
    """
    url = f"{NGX_PULSE_BASE_URL}/api/ngxdata/indices/asi/history"
    params = {
        "from": str(start_date),
        "to": str(end_date)
    }
    headers = {
        "X-API-Key": NGX_PULSE_API_KEY
    }
    try:
        response = requests.get(url, params=params, headers=headers, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        print(f"  Error fetching NGX ASI from {start_date} to {end_date}: {e}")
        raise

    if not data.get("success"):
        print(f"  NGX Pulse API returned an unsuccessful response: {data}")
        return []
    return data.get("history", [])

def upsert_asi_bulk(conn, rows: list[tuple]) -> None:
    """
    Bulk insert/update ASI rows.
    """
    if not rows:
        return
    try:
        with conn.cursor() as cur:
            execute_values(
                cur,
                """
                INSERT INTO raw.ngx_asi
                    (index_date, asi_value)
                VALUES %s
                ON CONFLICT (index_date)
                DO UPDATE SET asi_value = EXCLUDED.asi_value, loaded_at = NOW()
                """,
                rows
            )
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"  DB error while inserting ASI rows: {e}")
        raise

def run(days_back: int = 1) -> None:
    """
    Daily incremental run. Requests a single target date.
    If the market was closed (no data for that date), this is logged and the script exits without error.
    """
    target_date = date.today() - timedelta(days=days_back)
    conn = get_db_connection()
    try:
        history = fetch_asi_history(target_date, target_date)
        if not history:
            print(f"  No ASI value published for {target_date} (likely a non-trading day.)")
            return
        rows = [(date.fromisoformat(h["date"]), h["value"]) for h in history]
        upsert_asi_bulk(conn, rows)
        print(f"  Inserted ASI value for {target_date}: {rows[0][1]}")
    finally:
        conn.close()

def backfill(start_date: date, end_date:date) -> None:
    """
    One-time historical load using the time-series endpoint.
    """
    conn = get_db_connection()
    try:
        history = fetch_asi_history(start_date, end_date)
        rows = [(date.fromisoformat(h["date"]), h["value"]) for h in history]
        upsert_asi_bulk(conn, rows)
        print(f"  Backfilled NGX ASI from {start_date} to {end_date}: {len(rows)} rows")
    finally:
        conn.close()

if __name__ == "__main__":
    print("Running backfill for historical data (2020 to yesterday)")
    backfill(date(2020, 1, 1), date.today() - timedelta(days=1))
    print("Backfill complete.")
