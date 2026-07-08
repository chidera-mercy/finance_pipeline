-- Gold priced in naira.
--
-- Uses the same LOCF pattern as mart_returns_comparison: joins each
-- gold price to the most recent available USD/NGN rate on or before
-- that date, since gold and FX aren't necessarily quoted on the exact
-- same calendar days.
SELECT
    g.price_date,
    g.gold_close_usd,
    fx.rate AS usd_ngn_rate,
    ROUND(g.gold_close_usd * fx.rate, 2) AS gold_price_ngn_per_oz,
    ROUND(g.gold_close_usd * fx.rate / 31.1035, 2) AS gold_price_ngn_per_gram
FROM {{ ref('stg_gold_prices') }} g
LEFT JOIN LATERAL (
    SELECT rate
    FROM {{ ref('stg_exchange_rates') }}
    WHERE base_currency = 'USD' AND rate_date <= g.price_date
    ORDER BY rate_date DESC
    LIMIT 1
) fx ON TRUE
WHERE fx.rate IS NOT NULL
ORDER BY g.price_date
