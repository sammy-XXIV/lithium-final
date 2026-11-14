"""STEP 0: identify the filler for ~5 swaps. See HANDOFF.md section 4.

TODO:
1. GET {EXPLORER_BASE_URL}/transactions?numberOfTransactions=5 with Bearer EXPLORER_JWT. Save raw JSON to data/raw/spike/.
2. For each swap take nearTxHashes[0]; fetch the tx + receipts via NEAR RPC (EXPERIMENTAL_tx_status) or BigQuery (filter block_date).
3. List all accounts and token_diff/transfer events on intents.near (UNVERIFIED names).
4. Write docs/SPIKE_RESULT.md: IDENTIFIED / PARTIAL / NOT IDENTIFIABLE + raw evidence.
"""
raise NotImplementedError
