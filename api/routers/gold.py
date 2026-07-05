from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query

from api.database import get_db
from api.schemas import GoldPrice

router = APIRouter(prefix="/gold", tags=["gold"])


@router.get("/latest", response_model=GoldPrice)
def latest_gold_price(conn = Depends(get_db)):
    query = """
        SELECT price_date, close_usd
        FROM raw.gold_prices
        ORDER BY price_date DESC
        LIMIT 1
    """
    with conn.cursor() as cur:
        cur.execute(query)
        row = cur.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="No gold price data found")

    return GoldPrice(price_date=row[0], close_usd=row[1])

@router.get("/history", response_model=list[GoldPrice])
def gold_price_history(
    start: date = Query(..., description="Start date (inclusive), YYYY-MM-DD"),
    end: date = Query(..., description="End date (inclusive), YYYY-MM-DD"),
    limit: int = Query(1000, ge=1, le=5000),
    conn = Depends(get_db)
):
    if start > end:
        raise HTTPException(
            status_code=400,
            detail="start date must be <= end date"
        )

    query = """
        SELECT price_date, close_usd
        FROM raw.gold_prices
        WHERE price_date BETWEEN %s AND %s
        ORDER BY price_date
        LIMIT %s
    """
    with conn.cursor() as cur:
        cur.execute(query, (start, end, limit))
        rows = cur.fetchall()

    if not rows:
        raise HTTPException(status_code=404, detail="No gold price data found for that range")
    
    return [
        GoldPrice(price_date=r[0], close_usd=r[1])
        for r in rows
    ]
