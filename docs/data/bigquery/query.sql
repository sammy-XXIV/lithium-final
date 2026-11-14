WITH event_logs AS (
  SELECT
    block_date AS observed_date,
    EXTRACT(HOUR FROM block_timestamp_utc) AS utc_hour,
    receipt_id,
    status,
    SUBSTR(log_entry.element, LENGTH('EVENT_JSON:') + 1) AS event_json
  FROM `bigquery-public-data.crypto_near_mainnet_us.execution_outcomes`
  CROSS JOIN UNNEST(logs.list) AS log_entry
  WHERE block_date IN (
    DATE '2026-09-16', DATE '2026-09-24',
    DATE '2026-10-02', DATE '2026-10-10',
    DATE '2026-10-18', DATE '2026-10-26',
    DATE '2026-11-03', DATE '2026-11-11'
  )
    AND EXTRACT(HOUR FROM block_timestamp_utc) IN (0, 8, 16)
    AND EXTRACT(MINUTE FROM block_timestamp_utc) < 2
    AND executor_account_id = 'intents.near'
    AND STARTS_WITH(log_entry.element, 'EVENT_JSON:')
)
SELECT
  observed_date,
  utc_hour,
  JSON_VALUE(event_json, '$.standard') AS standard,
  JSON_VALUE(event_json, '$.version') AS schema_version,
  JSON_VALUE(event_json, '$.event') AS event_name,
  status,
  COUNT(*) AS event_log_count,
  COUNT(DISTINCT receipt_id) AS receipts_with_event
FROM event_logs
GROUP BY observed_date, utc_hour, standard, schema_version, event_name, status
ORDER BY observed_date, utc_hour, event_log_count DESC;
