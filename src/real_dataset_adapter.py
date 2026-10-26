"""Adapters for public and uploaded real-world A/B test datasets.

The Udacity/Kaggle-style e-commerce dataset is a public educational dataset,
not a verified production experiment. Its assignment/page mismatches and
repeated user IDs are excluded transparently before user-level inference.
"""
from __future__ import annotations

import pandas as pd

PUBLIC_AB_DATA_URL = (
    "https://raw.githubusercontent.com/beery4010/Analyze-AB-Test-Results/"
    "master/ab_data.csv"
)


def adapt_ecommerce_ab_dataset(raw: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Map common ecommerce A/B schema into Varianta's canonical schema.

    Expected source fields: user_id, timestamp, group, landing_page, converted.
    Rows with group/page mismatches, invalid assignments/outcomes, or repeated
    user IDs are removed with counts recorded in the returned audit metadata.
    No revenue values are fabricated; order_value is a neutral placeholder and
    `revenue_available` remains False in the audit metadata.
    """
    df = raw.copy()
    df.columns = [str(c).strip().lower() for c in df.columns]
    required = {"user_id", "timestamp", "group", "landing_page", "converted"}
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(
            "This public e-commerce adapter requires columns: user_id, timestamp, "
            "group, landing_page, converted. Missing: " + ", ".join(missing)
        )

    audit = {"source_rows": int(len(df)), "missing_required_columns": [],
             "invalid_outcome_rows_removed": 0, "group_page_mismatch_rows_removed": 0,
             "duplicate_user_rows_removed": 0, "invalid_timestamp_rows_removed": 0,
             "analysis_rows": 0, "revenue_available": False}

    df["group"] = df["group"].astype("string").str.strip().str.lower()
    df["landing_page"] = df["landing_page"].astype("string").str.strip().str.lower()
    df["converted"] = pd.to_numeric(df["converted"], errors="coerce")
    valid_outcome = df["converted"].isin([0, 1]) & df["user_id"].notna()
    audit["invalid_outcome_rows_removed"] = int((~valid_outcome).sum())
    df = df.loc[valid_outcome].copy()
    df["converted"] = df["converted"].astype(int)

    expected_page = df["group"].map({"control": "old_page", "treatment": "new_page"})
    valid_pair = expected_page.notna() & df["landing_page"].eq(expected_page)
    audit["group_page_mismatch_rows_removed"] = int((~valid_pair).sum())
    df = df.loc[valid_pair].copy()

    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce", utc=True)
    valid_time = df["timestamp"].notna()
    audit["invalid_timestamp_rows_removed"] = int((~valid_time).sum())
    df = df.loc[valid_time].copy()

    before_dedup = len(df)
    # The source contains repeated user IDs; retain the earliest eligible valid row.
    df = df.sort_values("timestamp").drop_duplicates("user_id", keep="first").copy()
    audit["duplicate_user_rows_removed"] = int(before_dedup - len(df))

    df["variant"] = df["group"].map({"control": "Control", "treatment": "Treatment"})
    df["assignment_timestamp"] = df["timestamp"]
    # The source only provides a conversion flag and visit timestamp; it does not
    # provide event-level timestamps, revenue, device or checkout instrumentation.
    df["event_timestamp"] = df["timestamp"]
    df["device_type"] = "Unknown"
    df["country"] = df["country"].astype(str) if "country" in df.columns else "Unknown"
    df["acquisition_channel"] = "Unknown"
    df["is_new_customer"] = False
    df["checkout_started"] = df["converted"].astype(bool)
    df["purchase_completed"] = df["converted"].astype(bool)
    df["order_value"] = 0.0
    df["refund_indicator"] = False
    df["checkout_error_indicator"] = False
    df["page_load_time_ms"] = 0.0
    df["experiment_eligible"] = True
    df["source_group"] = df["group"]
    df["visit_day"] = df["timestamp"].dt.day_name()
    df["landing_page"] = df["landing_page"].astype(str)
    df["experiment_id"] = "public_ecommerce_landing_page_ab"
    audit["analysis_rows"] = int(len(df))
    audit["analysis_users"] = int(df["user_id"].nunique())
    audit["conversion_events"] = int(df["converted"].sum())
    audit["control_users"] = int((df["variant"] == "Control").sum())
    audit["treatment_users"] = int((df["variant"] == "Treatment").sum())

    columns = [
        "user_id", "experiment_id", "variant", "assignment_timestamp", "event_timestamp",
        "device_type", "country", "acquisition_channel", "is_new_customer", "checkout_started",
        "purchase_completed", "order_value", "refund_indicator", "checkout_error_indicator",
        "page_load_time_ms", "experiment_eligible", "source_group", "landing_page", "converted", "visit_day",
    ]
    return df[columns].reset_index(drop=True), audit
