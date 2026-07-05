from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query

from api.database import get_db
from api.schemas import ExchangeRate

router = APIRouter(prefix="/rates", tags=["exchange-rates"])

ALLOWED_BASES = {"USD", "GBP", "EUR"}


@router.get("/latest", response_model=list[ExchangeRate])
def latest_rates(
    base: str | None = Query(None, description="Filter to a single base currency"),
    conn = Depends(get_db)
):
    if base is not None and base.upper() not in ALLOWED_BASES:
        raise HTTPException(
            status_code=400,
            detail=f"base must be one of {sorted(ALLOWED_BASES)}"
        )

    query = """
        SELECT DISTINCT ON (base_currency)
            base_currency, target_currency, rate, rate_date
        FROM raw.exchange_rates
        WHERE (%s IS NULL OR base_currency = %s)
        ORDER BY base_currency, rate_date DESC
    """
    base_upper = base.upper() if base else None
    with conn.cursor() as cur:
        cur.execute(query, (base_upper, base_upper))
        rows = cur.fetchall()

    if not rows:
        raise HTTPException(status_code=404, detail="No exchange rate data found")

    return [
        ExchangeRate(
            base_currency=r[0], target_currency=r[1], rate=r[2], rate_date=r[3]
        )
        for r in rows
    ]

@router.get("/history", response_model=list[ExchangeRate])
def rate_history(
    base: str = Query(..., description="Base currency, e.g. USD"),
    start: date = Query(..., description="Start date (inclusive), YYYY-MM-DD"),
    end: date = Query(..., description="End date (inclusive), YYYY-MM-DD"),
    limit: int = Query(1000, ge=1, le=5000),
    conn = Depends(get_db)
):
    base_upper = base.upper()

    if base_upper not in ALLOWED_BASES:
        raise HTTPException(
            status_code=400,
            detail=f"base must be one of {sorted(ALLOWED_BASES)}"
        )
    if start > end:
        raise HTTPException(
            status_code=400,
            detail="start date must be <= end date"
        )

    query = """
        SELECT base_currency, target_currency, rate, rate_date
        FROM raw.exchange_rates
        WHERE base_currency = %s 
            AND rate_date BETWEEN %s AND %s
        ORDER BY rate_date
        LIMIT %s
    """
    with conn.cursor() as cur:
        cur.execute(query, (base_upper, start, end, limit))
        rows = cur.fetchall()

    if not rows:
        raise HTTPException(status_code=404, detail="No exchange rate data found")
    
    return [
        ExchangeRate(base_currency=r[0], target_currency=r[1], rate=r[2], rate_date=r[3])
        for r in rows
    ]
