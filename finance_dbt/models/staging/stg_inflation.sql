SELECT
    id,
    country,
    year,
    inflation as inflation_rate_pct,
    loaded_at
FROM {{ source('raw', 'inflation') }}
WHERE inflation IS NOT NULL
