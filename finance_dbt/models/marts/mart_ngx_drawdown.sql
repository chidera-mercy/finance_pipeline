-- Drawdown analysis for the NGX All-Share Index:
-- for every trading day, how far below its running peak-to-date is the index?

SELECT
    index_date,
    asi_value,
    MAX(asi_value) OVER (
        ORDER BY index_date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS running_peak_to_date,
    ROUND(
        (
            asi_value - MAX(asi_value) OVER (
                ORDER BY index_date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
            )
        ) / MAX(asi_value) OVER (
            ORDER BY index_date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) * 100,
        2
    ) AS drawdown_from_peak_pct
FROM {{ ref('stg_ngx_asi') }}
ORDER BY index_date
