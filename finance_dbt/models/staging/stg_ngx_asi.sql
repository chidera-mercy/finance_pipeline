SELECT
    id,
    index_date,
    asi_value,
    loaded_at
FROM {{ source('raw', 'ngx_asi') }}
WHERE asi_value IS NOT NULL
    AND asi_value > 0
