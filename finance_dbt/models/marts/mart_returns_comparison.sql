-- Compares ₦1,000,000 invested in three assets: USD, gold, and Nigerian equities
WITH fx AS (
    SELECT
        rate_date AS price_date,
        rate      AS usd_ngn_rate
    FROM {{ ref('stg_exchange_rates') }}
    WHERE base_currency ='USD'
),
gold AS (
    SELECT
        price_date,
        gold_close_usd
    FROM {{ ref('stg_gold_prices') }}
),
ngx AS (
    SELECT
        index_date AS price_date,
        asi_value
        FROM {{ ref('stg_ngx_asi')}}
),
combined AS (
    SELECT
        fx.price_date,
        fx.usd_ngn_rate,
        gold.gold_close_usd,
        ngx.asi_value
    FROM fx
    INNER JOIN gold ON fx.price_date = gold.price_date
    INNER JOIN ngx  ON fx.price_date = ngx.price_date
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