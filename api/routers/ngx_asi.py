from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query

from api.database import get_db
from api.schemas import NgxAsiRecord

router = APIRouter(prefix="/ngx", tags=["ngx-asi"])


@router.get("/latest", response_model=NgxAsiRecord)
def latest_asi(conn = Depends(get_db)):
    query = """
        SELECT index_date, asi_value
        FROM raw.ngx_asi
        ORDER BY index_date DESC
        LIMIT 1
    """
    with conn.cursor() as cur:
        cur.execute(query)
        row = cur.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="No NGX ASI data found")

    return NgxAsiRecord(index_date=row[0], asi_value=row[1])

@router.get("/history", response_model=list[NgxAsiRecord])
def asi_history(
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
        SELECT index_date, asi_value
        FROM raw.ngx_asi
        WHERE index_date BETWEEN %s AND %s
        ORDER BY rate_date
        LIMIT %s
    """
    with conn.cursor() as cur:
        cur.execute(query, (start, end, limit))
        rows = cur.fetchall()

    if not rows:
        raise HTTPException(status_code=404, detail="No NGX ASI data found for that range")
    
    return [
        NgxAsiRecord(index_date=r[0], asi_value=r[1])
        for r in rows
    ]
