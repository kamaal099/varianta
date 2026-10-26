# Data dictionary

The synthetic generator emits one row per randomized eligible user. `purchase_completed` is the primary binary outcome. `order_value` is zero for non-purchasers and positive/skewed for purchasers. Timestamps are UTC. All data are simulated; no real customer data are included.

| Column | Type | Meaning |
|---|---|---|
| user_id | string | Stable user ID; expected unique |
| experiment_id | string | Experiment identifier |
| variant | category | Control or Treatment |
| assignment_timestamp | timestamp | Assignment time |
| event_timestamp | timestamp | Outcome observation time |
| device_type | category | Desktop, Mobile, Tablet |
| country | category | Simulated country |
| acquisition_channel | category | Marketing channel |
| is_new_customer | bool | New customer indicator |
| session_id | string | Simulated session identifier |
| checkout_started | bool | Checkout started |
| purchase_completed | bool | Purchase outcome |
| order_value | float | Order value, zero if no purchase |
| refund_indicator | bool | Simulated refund |
| checkout_error_indicator | bool | Simulated checkout error |
| page_load_time_ms | float | Simulated latency |
| experiment_eligible | bool | Eligible for analysis |
