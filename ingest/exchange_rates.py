"""
Ingests USD/NGN, GBP/NGN, and EUR/NGN exchange rates from the
Frankfurter API (https://api.frankfurter.dev).
No API key required.
"""
import os
from datetime import date, timedelta

from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import execute_values
import requests

load_dotenv()

FRANKFURTER_BASE_URL = "https://api.frankfurter.dev/v2"
BASE_QUOTE_PAIRS = [("USD", "NGN"), ("GBP", "NGN"), ("EUR", "NGN")]
REQUEST_TIMEOUT = 10
BACKFILL_TIMEOUT = 30

def get_db_connection():
    """
    Open a connection to the PostgresSQL database.
    """
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )

def fetch_rate_for_date(for_date: date, base: str, quote: str) -> float:
    """
    Fetch a single base/quote  exchange rate for a specific date.
    GET /v2/rates?date={YYYY-MM-DD}&base={base}&quotes={quote}
    """
    url = f"{FRANKFURTER_BASE_URL}/rates"
    params = {
        "date": str(for_date),
        "base": base,
        "quotes": quote
    }
    try:
        response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        data = response.json()
        return data[0]["rate"]
    except requests.exceptions.RequestException as e:
        print(f"  Error fetching {base}/{quote} for {for_date}: {e}")
        raise

def fetch_timeseries(start_date: date, end_date: date, base: str, quote: str) -> list:
    """
    Fetch a base/quote exchange rate time series.
    GET /v2/rates?from=YYYY-MM-DD&to=YYYY-MM-DD&base={base}&quotes={quote}
    """
    url = f"{FRANKFURTER_BASE_URL}/rates"
    params = {
        "from": str(start_date),
        "to": str(end_date),
        "base": base,
        "quotes": quote
    }
    try:
        response = requests.get(url, params=params, timeout=BACKFILL_TIMEOUT)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"  Error fetching {base}/{quote} from {start_date} to {end_date}: {e}")
        raise

def upsert_rate(conn, base: str, quote: str, rate: float, rate_date: date) -> None:
    """
    Inserts or update a single exchange rate row.
    """
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO raw.exchange_rates 
                    (base_currency, target_currency, rate, rate_date)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (base_currency, target_currency, rate_date)
                DO UPDATE SET rate = EXCLUDED.rate, loaded_at = NOW()
            """, (base, quote, rate, rate_date))
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"  DB error inserting {base}/{quote} for {rate_date}: {e}")
        raise

def upsert_rates_bulk(conn, rows: list[tuple]) -> None:
    """
    Bulk insert/update many exchange rate rows in one round trip.
    """
    if not rows:
        return
    try:
        with conn.cursor() as cur:
            execute_values(
                cur, 
                """
                INSERT INTO raw.exchange_rates
                    (base_currency, target_currency, rate, rate_date)
                VALUES %s
                ON CONFLICT (base_currency, target_currency, rate_date)
                DO UPDATE SET rate = EXCLUDED.rate, loaded_at = NOW()
                """, 
                rows
            )
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"  DB error during bulk insert: {e}")
        raise

def run(days_back: int = 1) -> None:
    """
    Daily incremental run; Fetches and stores yesterday's rates
    for all configured currency pairs.
    """
    target_date = date.today() - timedelta(days=days_back)
    conn = get_db_connection()

    try:
        for base, quote in BASE_QUOTE_PAIRS:
            rate = fetch_rate_for_date(target_date, base, quote)
            upsert_rate(conn, base, quote, rate, target_date)
            print(f"  Inserted {base}/{quote} = {rate} for {target_date}")
    finally:
        conn.close()

def backfill(start_date: date, end_date: date) -> None:
    """
    One-time historical load. Fetches the full time series for each
    currency pair and bulk-inserts it. Call this once to seed history.
    """
    conn = get_db_connection()

    try:
        for base, quote in BASE_QUOTE_PAIRS:
            try:
                data = fetch_timeseries(start_date, end_date, base, quote)
            except requests.exceptions.RequestException:
                continue

            rows = []
            for row in data:
                rows.append((base, quote, row["rate"], date.fromisoformat(row["date"])))

            upsert_rates_bulk(conn, rows)
            print(f"  Backfilled {base}/{quote} from {start_date} to {end_date}: {len(rows)} rows")
    finally:
        conn.close()

if __name__ == "__main__":
    print("Running backfill for historical data (2020 to yesterday)")
    backfill(date(2020, 1, 1), date.today() - timedelta(days=1))
    print("Backfill complete.")
