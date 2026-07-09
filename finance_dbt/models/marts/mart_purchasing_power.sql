-- Shows how ₦1,000,000 loses real value each year due to inflation
WITH base AS (
    SELECT
        year,
        inflation_rate_pct,
        COALESCE(
            EXP(
                SUM(LN(1 + inflation_rate_pct / 100.0))
                OVER (ORDER BY year ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING)
            ),
            1.0
        ) AS cumulative_inflation_factor
    FROM {{ ref('stg_inflation') }}
    WHERE year >= 2020
)
SELECT
    year,
    inflation_rate_pct,
    cumulative_inflation_factor,
    ROUND(1000000 / cumulative_inflation_factor, 2) as real_value_of_1m_naira
FROM base
ORDER BY year
