-- Monthly average exchange rates with year-over-year change
WITH monthly AS (
    SELECT
        DATE_TRUNC('month', rate_date) AS month,
        base_currency,
        AVG(rate) AS avg_monthly_rate
    FROM {{ ref('stg_exchange_rates')}}
    GROUP BY 1, 2
)
SELECT 
    month,
    base_currency,
    ROUND(avg_monthly_rate::NUMERIC, 2) AS avg_monthly_rate,
    ROUND(
        (avg_monthly_rate - LAG(avg_monthly_rate, 12)
            OVER (PARTITION BY base_currency ORDER BY month))
        / nullif(LAG(avg_monthly_rate, 12)
            OVER (PARTITION BY base_currency ORDER BY month), 0) * 100,
        2
    ) as yoy_change_pct
FROM monthly
ORDER BY base_currency, month