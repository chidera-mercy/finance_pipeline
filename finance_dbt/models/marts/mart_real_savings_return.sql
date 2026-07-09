-- Compares the nominal deposit interest rate to inflation each year
-- to show whether savers gained or lost in real terms.
SELECT 
    i.year,
    i.inflation_rate_pct,
    r.deposit_rate_pct,
    ROUND(r.deposit_rate_pct - i.inflation_rate_pct, 2) AS approx_real_return_pct,
    ROUND(
        (
            (1 + r.deposit_rate_pct / 100.0)
            / (1 + i.inflation_rate_pct / 100.0)
            - 1
        ) * 100,
        2
    ) AS fisher_real_return_pct,
    CASE
        WHEN r.deposit_rate_pct > i.inflation_rate_pct THEN 'positive_real_return'
        ELSE 'negative_real_return'
    END AS real_return_flag 
FROM {{ ref('stg_inflation') }} i
INNER JOIN {{ ref('stg_interest_rates') }} r
    ON i.year = r.year
ORDER BY i.year
