-- One row per year combining every data source into a single summary:
-- year-end USD/NGN rate and its YoY change,
-- year-end gold price and YoY change, 
-- year-end NGX ASI and YoY return, 
-- annual inflation, and annual deposit rate. 

WITH fx_year_end AS (
    SELECT DISTINCT ON (EXTRACT(YEAR FROM rate_date))
        EXTRACT(YEAR FROM rate_date)::INT AS year,
        rate AS year_end_usd_ngn
    FROM {{ ref('stg_exchange_rates') }}
    WHERE base_currency = 'USD'
    ORDER BY EXTRACT(YEAR FROM rate_date), rate_date DESC
),
gold_year_end AS (
    SELECT DISTINCT ON (EXTRACT(YEAR FROM price_date))
        EXTRACT(YEAR FROM price_date)::INT AS year,
        glose_close_usd AS year_end_gold_usd
    FROM {{ ref('stg_gold_prices') }}
    ORDER BY EXTRACT(YEAR FROM price_date), price_date DESC
),
asi_year_end AS (
    SELECT DISTINCT ON (EXTRACT(YEAR FROM index_date))
        EXTRACT(YEAR FROM index_date),
        asi_value AS yeat_end_asi
    FROM {{ ref('stg_ngx_asi') }}
    ORDER BY EXTRACT(YEAR FROM index_date), index_date DESC
),
combined AS (
    SELECT
        a.year,
        i.inflation_rate_pct,
        r.deposit_rate_pct,
        fx.year_end_usd_ngn,
        g.year_end_gold_usd,
        a.year_end_asi
    FROM asi_year_end a
    LEFT JOIN {{ ref('stg_inflation') }} i ON a.year = i.year
    LEFT JOIN {{ ref('stg_interest_rates') }} r ON a.year = r.year
    LEFT JOIN fx_year_end fx ON a.year = fx.year
    LEFT JOIN gold_year_end g ON a.year = g.year
)
SELECT 
    year,
    inflation_rate_pct,
    deposit_rate_pct,
    year_end_usd_ngn,
    ROUND(
        (year_end_usd_ngn - LAG(year_end_usd_ngn) OVER (ORDER BY year))
        / NULLIF(LAG(year_end_usd_ngn) OVER (ORDER BY year), 0) * 100,
        2
    ) AS naira_depreciation_yoy_pct,
    year_end_gold_usd,
    ROUND(
        (year_end_gold_usd - LAG(year_end_gold_usd) OVER (ORDER BY year))
        / NULLIF(LAG(year_end_gold_usd) OVER (ORDER BY year), 0) * 100,
        2
    ) AS gold_return_yoy_pct,
    year_end_asi,
    ROUND(
        (year_end_asi - LAG(year_end_asi) OVER (ORDER BY year))
        / NULLIF(LAG(year_end_asi) OVER (ORDER BY year), 0) * 100,
        2
    ) AS asi_return_yoy_pct
FROM combined
ORDER BY year
