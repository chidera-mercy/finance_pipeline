-- Cleans and lightly filters raw exchange rate data
SELECT
    id,
    base_currency,
    target_currency,
    rate,
    rate_date,
    loaded_at
FROM {{ source('raw', 'exchange_rates') }}
WHERE rate IS NOT NULL
    AND rate > 0
