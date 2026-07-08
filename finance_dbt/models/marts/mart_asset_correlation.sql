-- Correlation between monthly returns of USD/NGN, gold, and the NGX ASI. 
-- "if the naira weakens, does gold or the stock market tend to move with it or against it?" 
-- This is the basis of any diversification argument 
-- (e.g. "gold is a good naira hedge because it's weakly/negatively correlated with the currency") 

-- Resamples all three series to month-end values before computing returns, 
-- since correlating raw daily series across sources with different 
-- trading calendars would be comparing mismatched dates.

WITH bounds AS (
    SELECT
        LEAST(
            MIN(rate_date), MIN(price_date), MIN(index_date)
        ) AS min_date,
        GREATEST(
            MAX(rate_date), MAX(price_date), MAX(index_date)
        ) AS max_date
    FROM {{ ref('stg_exchange_rates') }}
    CROSS JOIN {{ ref('stg_gold_prices') }}
    CROSS JOIN {{ ref('stg_ngx_asi') }}
),
month_ends AS (
    SELECT (generate_series(
        DATE_TRUNC('month', min_date),
        DATE_TRUNC('month', max_date),
        interval '1 month'
    ) + interval '1 month' - interval '1 day')::date AS month_end
    FROM bounds
),
fx_monthly AS (
    SELECT 
        me.month_end, 
        fx_rate AS usd_ngn_rate
    FROM month_ends me
    LEFT JOIN LATERAL (
        SELECT rate 
        FROM {{ ref('stg_exchange_rates') }}
        WHERE base_currency = 'USD' AND rate_date <= me.month_end
        ORDER BY rate_date DESC LIMIT 1
    ) fx ON TRUE
),
gold_monthly AS (
    SELECT 
        me.month_end, 
        g.gold_close_usd
    FROM month_ends me
    LEFT JOIN LATERAL (
        SELECT gold_close_usd 
        FROM {{ ref('stg_gold_prices') }}
        WHERE price_date <= me.month_end
        ORDER BY price_date DESC LIMIT 1
    ) g ON TRUE
),
asi_monthly AS (
    SELECT 
        me.month_end, 
        a.asi_value
    FROM month_ends me
    LEFT JOIN LATERAL (
        SELECT asi_value 
        FROM {{ ref('stg_ngx_asi') }}
        WHERE index_date <= me.month_end
        ORDER BY index_date DESC LIMIT 1
    ) a ON TRUE
),
combined AS (
    SELECT
        f.month_end,
        f.usd_ngn_rate,
        g.gold_close_usd,
        a.asi_value
    FROM fx_monthy f
    JOIN gold_monthly g USING (month_end)
    JOIN asi_monthly a USING (month_end)
    WHERE f.usd_ngn_rate IS NOT NULL
        AND g.gold_close_usd IS NOT NULL
        AND a.asi_value IS NOT NULL
),
monthly_returns AS (
    SELECT
        month_end,
        usd_ngn_rate / LAG(usd_ngn_rate) OVER (ORDER BY month_end) - 1 AS usd_return,
        gold_close_usd / LAG(gold_close_usd) OVER (ORDER BY month_end) - 1 AS gold_return,
        asi_value / LAG(asi_value) OVER (ORDER BY month_end) - 1 AS asi_return
    FROM combined
)
SELECT
    ROUND(CORR(usd_return, gold_return)::NUMERIC, 3) AS usd_gold_correlation,
    ROUND(CORR(usd_return, asi_return)::NUMERIC, 3) AS usd_asi_correlation,
    ROUND(CORR(gold_return, asi_return)::NUMERIC, 3) AS gold_asi_correlation,
    COUNT(*) AS months_used
FROM monthly_returns
WHERE usd_return IS NOT NULL
