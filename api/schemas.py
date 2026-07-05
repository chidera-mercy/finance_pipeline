from datetime import date

from pydantic import BaseModel

class ExchangeRate(BaseModel):
    base_currency: str
    target_currency: str
    rate: float
    rate_date: date


class GoldPrice(BaseModel):
    price_date: date
    close_usd: float


class InflationRecord(BaseModel):
    country: str
    year: int
    inflation_rate_pct: float


class InterestRateRecord(BaseModel):
    country: str
    year: int
    rate_type: str
    rate_pct: float


class NgxAsiRecord(BaseModel):
    index_date: date
    asi_value: float


class Indicator(BaseModel):
    id: str
    description: str
    source: str
    frequency: str


class PurchasingPowerRecord(BaseModel):
    year: int
    inflation_rate_pct: float
    cummulative_inflation_factor: float
    real_value_of_1m_naira: float


class RealSavingsReturnRecord(BaseModel):
    year: int
    inflation_rate_pct: float
    deposit_rate_pct: float
    real_return_pct: float
    real_return_flag: str


class ReturnsComparisonRecord(BaseModel):
    price_date: date
    usd_ngn_rate: float
    gold_close_usd: float
    asi_value: float
    usd_position_ngn: float
    gold_position_ngn: float
    ngx_position_ngn: float


class FxVolatilityRecord(BaseModel):
    base_currency: str
    rate_date: date
    rate: float
    rolling_30d_annualized_volatility_pct: float | None = None


class GoldNgnRecord(BaseModel):
    price_date: date
    gold_close_usd: float
    usd_ngn_rate: float
    gold_price_ngn_per_oz: float
    gold_price_ngn_per_gram: float


class NgxDrawdownRecord(BaseModel):
    index_date: date
    asi_value: float
    running_peak_to_date: float
    drawdown_from_peak_pct: float


class AnnualSummaryRecord(BaseModel):
    year: int
    inflation_rate_pct: float | None = None
    deposit_rate_pct: float | None 
    year_end_usd_ngn: float | None  = None
    naira_depreciation_yoy_pct: float | None = None
    year_end_gold_usd: float | None = None
    gold_return_yoy_pct:float | None = None
    year_end_asi: float | None = None
    asi_return_yoy_pct: float | None = None


class AssetCorrelationRecord(BaseModel):
    usd_gold_correlation: float | None = None
    usd_asi_correlation: float | None = None
    gold_asi_correlation: float | None = None
    months_used: int
