-- Metadata only: inspect available dates before choosing transaction partitions.
-- Confirmed dataset location: us-east1. This view has no block_date column.
SELECT
  table_name,
  MIN(partition_id) AS first_partition,
  MAX(partition_id) AS latest_partition
FROM `bigquery-public-data.crypto_near_mainnet_us.INFORMATION_SCHEMA.PARTITIONS`
WHERE table_name IN (
  'transactions', 'execution_outcomes', 'receipt_details', 'receipt_origin_transaction'
)
  AND REGEXP_CONTAINS(partition_id, r'^[0-9]{8}$')
GROUP BY table_name
ORDER BY table_name;
