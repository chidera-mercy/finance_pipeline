from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query

from api.database import get_db
from api.schemas import (
    PurchasingPowerRecord,
    RealSavingsReturnRecord,
    ReturnsComparisonRecord,
    FxVolatilityRecord,
    GoldNgnRecord,
    NgxDrawdownRecord,
    AnnualSummaryRecord,
    AssetCorrelationRecord
)

ALLOWED_BASES = ["USD", "GBP", "EUR"]

router = APIRouter(prefix="/insights", tags=["insights"])


@router.get("/purchasing-power", response_model=list[PurchasingPowerRecord])
def purchasing_power(
    start_year: int | None = Query(None),
    end_year: int | None = Query(None),
    conn = Depends(get_db)
):
    if start_year and end_year and start_year > end_year:
        raise HTTPException(status_code=400, detail="start_year must be <= end_year")
    
    query = """
        SELECT year, inflation_rate_pct, 
            cummulative_inflation_factor, real_value_of_1m_naira
        FROM analytics.mart_purchasing_power
        WHERE (%s IS NULL OR year >= %s)
            AND (%s IS NULL OR year <= %s)
        ORDER BY year
    """
    with conn.cursor() as cur:
        cur.execute(query, (start_year, start_year, end_year, end_year))
        rows = cur.fetchall()
    
    if not rows:
        raise HTTPException(status_code=404, detail="No purchasing power data found")
    
    return [
        PurchasingPowerRecord(
            year=r[0],
            inflation_rate_pct=r[1],
            cummulative_inflation_factor=r[2],
            real_value_of_1m_naira=r[3]
        )
        for r in rows
    ]

@router.get("/real-savings-return", response_model=list[RealSavingsReturnRecord])
def real_savings_return(conn=Depends(get_db)):
    query = """
        SELECT year, inflation_rate_pct, deposit_rate_pct, 
            real_return_pct, real_return_flag
        FROM analytics.mart_real_savings_return
        ORDER BY year
    """
    with conn.cursor() as cur:
        cur.execute(query)
        rows = cur.fetchall()
    
    if not rows:
        raise HTTPException(status_code=404, detail="No real savings return data found")
    
    return [
        RealSavingsReturnRecord(
            year=r[0],
            inflation_rate_pct=r[1],
            deposit_rate_pct=r[2],
            real_return_pct=r[3],
            real_return_flag=r[4]
        )
        for r in rows
    ]

@router.get("/returns-comparison", response_model=list[ReturnsComparisonRecord])
def returns_comparison(
    start: date | None = Query(None),
    end: date | None = Query(None),
    limit: int = Query(1000, ge=1, le=5000),
    conn=Depends(get_db)
):
    if start and end and start > end:
        raise HTTPException(status_code=400, detail="start must be <= end")
    
    query = """
        SELECT price_date, usd_ngn_rate, gold_close_usd, asi_value, 
            usd_position_ngn, gold_position_ngn, ngx_position_ngn
        FROM analytics.mart_returns_comparison
        WHERE (%s IS NULL OR price_date >= %s)
            AND (%s IS NULL OR price_date <= %s)
        ORDER BY price_date
        LIMIT %s
    """
    with conn.cursor() as cur:
        cur.execute(query, (start, start, end, end, limit))
        rows = cur.fetchall()
    
    if not rows:
        raise HTTPException(status_code=404, detail="No returns comparison data found")
    
    return [
        ReturnsComparisonRecord(
            price_date=r[0],
            usd_ngn_rate=r[1],
            gold_close_usd=r[2], 
            asi_value=r[3], 
            usd_position_ngn=r[4], 
            gold_position_ngn=r[5], 
            ngx_position_ngn=r[6]
        )
        for r in rows
    ]

@router.get("/fx-volatility", response_model=list[FxVolatilityRecord])
def fx_volatility(
    base: str | None = Query(None, description="Filter to single base currency"),
    start: date | None = Query(None),
    end: date | None = Query(None),
    limit: int = Query(1000, ge=1, le=5000),
    conn=Depends(get_db)
):
    if base is not None and base.upper() not in ALLOWED_BASES:
        raise HTTPException(
            status_code=400, 
            detail=f"base must be one of {ALLOWED_BASES}"
        )
    if start and end and start > end:
        raise HTTPException(status_code=400, detail="start must be <= end")
    
    base = base.upper() if base else None

    query = """
        SELECT base_currency, rate_date, rate, rolling_30d_annualized_volatility_pct
        FROM analytics.mart_fx_volatility
        WHERE (%s IS NULL OR base_currency = %s)
            AND (%s IS NULL OR rate_date >= %s)
            AND (%s IS NULL OR rate_date <= %s)
        ORDER BY base_currency, rate_date
        LIMIT %s
    """
    with conn.cursor() as cur:
        cur.execute(query, (base, base, start, start, end, end, limit))
        rows = cur.fetchall()
    
    if not rows:
        raise HTTPException(status_code=404, detail="No FX volatility data found")
    
    return [
        FxVolatilityRecord(
            base_currency=r[0], 
            rate_date=r[1], 
            rate=r[2], 
            rolling_30d_annualized_volatility_pct=r[3]
        )
        for r in rows
    ]

@router.get("/gold-ngn", response_model=list[GoldNgnRecord])
def gold_ngn(
    start: date | None = Query(None),
    end: date | None = Query(None),
    limit: int = Query(1000, ge=1, le=5000),
    conn=Depends(get_db)
):
    if start and end and start > end:
        raise HTTPException(status_code=400, detail="start must be <= end")
    
    query = """
        SELECT price_date, gold_close_usd, usd_ngn_rate, 
            gold_price_ngn_per_oz, gold_price_ngn_per_gram
        FROM analytics.mart_gold_ngn
        WHERE (%s IS NULL OR price_date >= %s)
            AND (%s IS NULL OR price_date <= %s)
        ORDER BY price_date
        LIMIT %s
    """
    with conn.cursor() as cur:
        cur.execute(query, (start, start, end, end, limit))
        rows = cur.fetchall()
    
    if not rows:
        raise HTTPException(status_code=404, detail="No gold NGN dat found")
    
    return [
        GoldNgnRecord(
            price_date=r[0], 
            gold_close_usd=r[1], 
            usd_ngn_rate=r[2],
            gold_price_ngn_per_oz=r[3], 
            gold_price_ngn_per_gram=r[4],
        )
        for r in rows
    ]


@router.get("/ngx-drawdown", response_model=list[NgxDrawdownRecord])
def ngx_drawdown(
    start: date | None = Query(None),
    end: date | None = Query(None),
    limit: int = Query(1000, ge=1, le=5000),
    conn=Depends(get_db),
):
    if start and end and start > end:
        raise HTTPException(status_code=400, detail="start must be <= end")

    query = """
        SELECT index_date, asi_value, running_peak_to_date, drawdown_from_peak_pct
        FROM analytics.mart_ngx_drawdown
        WHERE (%s IS NULL OR index_date >= %s)
            AND (%s IS NULL OR index_date <= %s)
        ORDER BY index_date
        LIMIT %s
    """
    with conn.cursor() as cur:
        cur.execute(query, (start, start, end, end, limit))
        rows = cur.fetchall()

    if not rows:
        raise HTTPException(status_code=404, detail="No NGX drawdown data found")

    return [
        NgxDrawdownRecord(
            index_date=r[0], 
            asi_value=r[1], 
            running_peak_to_date=r[2],
            drawdown_from_peak_pct=r[3],
        )
        for r in rows
    ]


@router.get("/annual-summary", response_model=list[AnnualSummaryRecord])
def annual_summary(
    start_year: int | None = Query(None),
    end_year: int | None = Query(None),
    conn=Depends(get_db),
):
    if start_year and end_year and start_year > end_year:
        raise HTTPException(status_code=400, detail="start_year must be <= end_year")

    query = """
        SELECT year, inflation_rate_pct, deposit_rate_pct,
            year_end_usd_ngn, naira_depreciation_yoy_pct, 
            year_end_gold_usd, gold_return_yoy_pct, 
            year_end_asi, asi_return_yoy_pct
        FROM analytics.mart_annual_summary
        WHERE (%s IS NULL OR year >= %s)
            AND (%s IS NULL OR year <= %s)
        ORDER BY year
    """
    with conn.cursor() as cur:
        cur.execute(query, (start_year, start_year, end_year, end_year))
        rows = cur.fetchall()

    if not rows:
        raise HTTPException(status_code=404, detail="No annual summary data found")

    return [
        AnnualSummaryRecord(
            year=r[0], 
            inflation_rate_pct=r[1], 
            deposit_rate_pct=r[2],
            year_end_usd_ngn=r[3], 
            naira_depreciation_yoy_pct=r[4],
            year_end_gold_usd=r[5], 
            gold_return_yoy_pct=r[6],
            year_end_asi=r[7], 
            asi_return_yoy_pct=r[8],
        )
        for r in rows
    ]


@router.get("/asset-correlation", response_model=AssetCorrelationRecord)
def asset_correlation(conn=Depends(get_db)):
    query = """
        SELECT usd_gold_correlation, usd_asi_correlation, 
            gold_asi_correlation, months_used
        FROM analytics.mart_asset_correlation
    """
    with conn.cursor() as cur:
        cur.execute(query)
        row = cur.fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="No asset correlation data found")

    return AssetCorrelationRecord(
        usd_gold_correlation=row[0], 
        usd_asi_correlation=row[1],
        gold_asi_correlation=row[2],
        months_used=row[3],
    )
