-- Rolling 30-day annualised volatility of daily FX log-returns, per currency pair. 
-- "how risky/turbulent has the naira's exchange rate been recently, and is
-- it getting calmer or more volatile?" 
--
-- log-return is used (not simple % change) because log-returns are
-- additive across time and are the standard basis for volatility
-- calculations. Annualising with sqrt(252) follows the usual
-- trading-day convention.

WITH daily_returns AS (
    SELECT
        base_currency,
        rate_date,
        rate,
        LN(rate / NULLIF(LAG(rate) OVER (PARTITION BY base_currency ORDER BY rate_date), 0)) AS log_return
    FROM {{ ref('stg_exchange_rates') }}
)
SELECT
    base_currency,
    rate_date,
    rate,
    ROUND(
        (
            STDDEV_SAMP(log_return) OVER (
                PARTITION BY base_currency
                ORDER BY rate_date
                ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
            ) * SQRT(252) * 100
        )::NUMERIC,
        2
    ) AS rolling_30d_annualized_volatility_pct
FROM daily_returns
WHERE log_return IS NOT NULL
ORDER BY base_currency, rate_date
