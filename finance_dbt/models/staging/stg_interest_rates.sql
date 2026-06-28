SELECT
    id,
    country,
    year,
    rate_type,
    rate_pct AS deposit_rate_pct,
    loaded_at
FROM {{ source('raw', 'interest_rates') }}
WHERE rate_pct IS NOT NULL
    AND rate_type = 'deposit'
