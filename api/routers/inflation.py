from fastapi import APIRouter, Depends, HTTPException, Query

from api.database import get_db
from api.schemas import InflationRecord

router = APIRouter(prefix="/inflation", tags=["inflation"])


@router.get("/latest", response_model=InflationRecord)
def latest_inflation(
    country: str = Query("NG", description="ISO country code"),
    conn = Depends(get_db)
):
    query = """
        SELECT country, year, inflation
        FROM raw.inflation
        WHERE country = %s
        ORDER BY year DESC
        LIMIT 1
    """
    with conn.cursor() as cur:
        cur.execute(query, (country.upper()))
        row = cur.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="No inflation data found")

    return InflationRecord(country=row[0], year=row[1], inflation_rate_pct=row[2])

@router.get("", response_model=list[InflationRecord])
def inflation_series(
    country: str = Query("NG", description="ISO country code"),
    start_year: int | None = Query(None),
    end_year: int | None = Query(None),
    conn = Depends(get_db)
):
    if start_year and end_year and start_year > end_year:
        raise HTTPException(
            status_code=400,
            detail="start year must be <= end year"
        )

    query = """
        SELECT country, year, inflation
        FROM raw.inflation
        WHERE country = %s
            AND (%s IS NULL OR year >= %s)
            AND (%s IS NULL OR year <= %s)
        ORDER BY year
    """
    with conn.cursor() as cur:
        cur.execute(query, (country, start_year, start_year, end_year, end_year))
        rows = cur.fetchall()

    if not rows:
        raise HTTPException(status_code=404, detail="No inflation data found")
    
    return [
        InflationRecord(country=r[0], year=r[1], inflation_rate_pct=r[2])
        for r in rows
    ]
