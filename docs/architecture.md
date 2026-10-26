# Architecture and data flow

1. The user selects deterministic synthetic data or uploads a CSV.
2. Schema validation stops the application if required fields are absent.
3. Integrity checks report missing values, duplicates, variant issues, timestamp anomalies, outcome inconsistencies, sample-ratio mismatch, and low sample sizes.
4. Statistical modules compute conversion and revenue summaries outside Streamlit presentation code.
5. Segment analysis produces exploratory subgroup estimates with adjusted p-values.
6. The decision engine returns a transparent outcome and next action.
7. JSON/CSV reports are downloadable. Analysis metadata is recorded in local DuckDB.

The application intentionally avoids services and credentials. Before production use, add authentication, access controls, retention policies, formal experiment configuration versioning, exposure logging, prespecified guardrail non-inferiority tests, and independent statistical review.
