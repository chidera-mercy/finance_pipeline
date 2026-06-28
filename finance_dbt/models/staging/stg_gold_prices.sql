SELECT
    id,
    price_date,
    close_usd as gold_close_usd,
    source,
    loaded_at
FROM {{ source('raw', 'gold_prices') }}
WHERE close_usd IS NOT NULL
    AND close_usd > 0
