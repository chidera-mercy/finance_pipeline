-- Shows how ₦1,000,000 loses real value each year due to inflation
WITH base AS (
    SELECT
        year,
        inflation_rate_pct,
        EXP(SUM(LN(1 + inflation_rate_pct / 100.0))
            OVER (ORDER BY year)) AS cumulative_inflation_factor
    FROM {{ ref('stg_inflation') }}
    WHERE year >= 2019
)
SELECT
    year,
    inflation_rate_pct,
    cumulative_inflation_factor,
    ROUND(1000000 / cumulative_inflation_factor, 2) as real_value_of_1m_naira
FROM base
ORDER BY year