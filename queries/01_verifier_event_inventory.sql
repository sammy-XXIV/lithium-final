-- One declared two-minute observation window. Counts verifier log events, not swaps.
-- The block_date predicate prunes partitions; timestamp filters define the window.
-- All execution statuses remain visible in separate groups.
WITH event_logs AS (
  SELECT
    receipt_id,
    status,
    SUBSTR(log_entry.element, LENGTH('EVENT_JSON:') + 1) AS event_json
  FROM `bigquery-public-data.crypto_near_mainnet_us.execution_outcomes`
  CROSS JOIN UNNEST(logs.list) AS log_entry
  WHERE block_date = DATE '2026-11-11'
    AND block_timestamp_utc >= TIMESTAMP '2026-11-11 16:00:00+00'
    AND block_timestamp_utc < TIMESTAMP '2026-11-11 16:02:00+00'
    AND executor_account_id = 'intents.near'
    AND STARTS_WITH(log_entry.element, 'EVENT_JSON:')
)
SELECT
  JSON_VALUE(event_json, '$.standard') AS standard,
  JSON_VALUE(event_json, '$.version') AS schema_version,
  JSON_VALUE(event_json, '$.event') AS event_name,
  status,
  COUNT(*) AS event_log_count,
  COUNT(DISTINCT receipt_id) AS receipts_with_event
FROM event_logs
GROUP BY standard, schema_version, event_name, status
ORDER BY event_log_count DESC;
