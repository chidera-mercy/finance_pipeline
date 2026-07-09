-- Compares ₦1,000,000 invested in three assets: USD, gold, and Nigerian equities
--
-- Builds a daily calendar spine and carries the last known value forward (LOCF)
-- for each series via a LATERAL join, so every calendar day is represented 
-- using the most recent available price for series that don't update daily 
-- (i.e. weekends/holidays for NGX show the last trading value).
WITH bounds AS (
    SELECT
        LEAST(MIN(rate_date), MIN(price_date), MIN(index_date)) AS min_date,
        GREATEST(MAX(rate_date), MAX(price_date), MAX(index_date)) AS max_date
    FROM {{ ref('stg_exchange_rates') }}
    CROSS JOIN {{ ref('stg_gold_prices') }}
    CROSS JOIN {{ ref('stg_ngx_asi') }}
),
calendar AS (
    SELECT generate_series(min_date, max_date, interval '1 day')::date AS cal_date
    FROM bounds
),
fx_filled AS (
    SELECT c.cal_date, fx.rate AS usd_ngn_rate
    FROM calendar c
    LEFT JOIN LATERAL (
        SELECT rate
        FROM {{ ref('stg_exchange_rates') }}
        WHERE base_currency = 'USD' AND rate_date <= c.cal_date
        ORDER BY rate_date DESC
        LIMIT 1
    ) fx ON TRUE
),
gold_filled AS (
    SELECT c.cal_date, g.gold_close_usd
    FROM calendar c
    LEFT JOIN LATERAL (
        SELECT gold_close_usd
        FROM {{ ref('stg_gold_prices') }}
        WHERE price_date <= c.cal_date
        ORDER BY price_date DESC
        LIMIT 1
    ) g ON TRUE
),
asi_filled AS (
    SELECT c.cal_date, a.asi_value
    FROM calendar c
    LEFT JOIN LATERAL (
        SELECT asi_value
        FROM {{ ref('stg_ngx_asi') }}
        WHERE index_date <= c.cal_date
        ORDER BY index_date DESC
        LIMIT 1
    ) a ON TRUE
),
combined AS (
    SELECT
        f.cal_date AS price_date,
        f.usd_ngn_rate,
        g.gold_close_usd,
        a.asi_value
    FROM fx_filled f
    JOIN gold_filled g USING (cal_date)
    JOIN asi_filled a USING (cal_date)
    -- drop only the leading days before any series has a first value yet
    WHERE f.usd_ngn_rate IS NOT NULL
        AND g.gold_close_usd IS NOT NULL
        AND a.asi_value IS NOT NULL
),
anchors AS (
    SELECT 
        price_date     AS anchor_date,
        usd_ngn_rate   AS anchor_usd_ngn,
        gold_close_usd AS anchor_gold_usd,
        asi_value      AS anchor_asi
    FROM combined
    ORDER BY price_date
    LIMIT 1
)

SELECT
    c.price_date,
    c.usd_ngn_rate,
    c.gold_close_usd,
    c.asi_value,

    ROUND(
        (1000000.0 / a.anchor_usd_ngn) * c.usd_ngn_rate,
        2
    ) AS usd_position_ngn,

    ROUND(
        (1000000.0 / a.anchor_usd_ngn / a.anchor_gold_usd)
        * c.gold_close_usd * c.usd_ngn_rate,
        2
    ) AS gold_position_ngn,

    ROUND(
        (1000000.0 / a.anchor_asi) * c.asi_value,
        2
    ) AS ngx_position_ngn

FROM combined c
CROSS JOIN anchors a
ORDER BY c.price_date
