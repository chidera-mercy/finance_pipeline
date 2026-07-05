from fastapi import APIRouter

from api.schemas import Indicator

router = APIRouter(tags=["indicators"])

_INDICATORS = [
    Indicator(
        id="exchange_rates",
        description="USD/NGN, GBP/NGN, EUR/NGN exchange rates",
        source="Franfurter API",
        frequency="daily"
    ),
    Indicator(
        id="gold_prices",
        description="Gold spot price, USD per troy ounce",
        source="Stooq (backfill) / GoldAPI.io (daily)",
        frequency="daily",
    ),
    Indicator(
        id="inflation",
        description="Nigeria annual CPI inflation (%)",
        source="World Bank API",
        frequency="annual",
    ),
    Indicator(
        id="interest_rates",
        description="Nigeria annual deposit interest rate (%)",
        source="World Bank API",
        frequency="annual",
    ),
    Indicator(
        id="ngx_asi",
        description="NGX All-Share Index",
        source="NGX Pulse API",
        frequency="daily (trading days only)",
    )
]

@router.get("/indicators", response_model=list[Indicator])
def list_indicators():
    return _INDICATORS
