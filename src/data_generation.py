"""Reproducible synthetic experiment data generator."""
import numpy as np
import pandas as pd

def generate_experiment_data(n_users=12000, baseline_rate=0.12, treatment_effect=0.015, seed=42):
    """Generate one row per randomized user with user-level outcomes."""
    rng = np.random.default_rng(seed)
    n_control = n_users // 2
    n_treatment = n_users - n_control
    variants = np.array(["Control"] * n_control + ["Treatment"] * n_treatment)
    rng.shuffle(variants)
    device = rng.choice(["Desktop", "Mobile", "Tablet"], n_users, p=[.34,.59,.07])
    country = rng.choice(["US","GB","CA","IN","DE"], n_users, p=[.52,.14,.12,.14,.08])
    channel = rng.choice(["Paid Search","Organic","Email","Social","Direct"], n_users, p=[.27,.26,.13,.14,.20])
    new_customer = rng.random(n_users) < .43
    assignment = pd.Timestamp("2026-01-01", tz="UTC") + pd.to_timedelta(rng.integers(0, 14*24*60, n_users), unit="m")
    started = rng.random(n_users) < .76
    probabilities = np.where(variants == "Treatment", baseline_rate + treatment_effect, baseline_rate)
    probabilities = np.clip(probabilities, 0, .95)
    # Conversion is defined per eligible randomized user; any purchaser necessarily started checkout.
    purchased = rng.random(n_users) < probabilities
    started = started | purchased
    order_value = np.where(purchased, rng.lognormal(mean=3.65, sigma=.65, size=n_users), 0.0)
    refund = purchased & (rng.random(n_users) < .045)
    errors = rng.random(n_users) < np.where(variants == "Treatment", .035, .04)
    load_time = np.clip(rng.lognormal(mean=6.15, sigma=.42, size=n_users), 150, 12000)
    event_time = assignment + pd.to_timedelta(rng.integers(0, 7*24*60, n_users), unit="m")
    return pd.DataFrame({
        "user_id":[f"user_{i:07d}" for i in range(n_users)],
        "experiment_id":"checkout_redesign_v1",
        "variant":variants,
        "assignment_timestamp":assignment,
        "event_timestamp":event_time,
        "device_type":device,
        "country":country,
        "acquisition_channel":channel,
        "is_new_customer":new_customer,
        "session_id":[f"session_{i:07d}" for i in range(n_users)],
        "checkout_started":started,
        "purchase_completed":purchased,
        "order_value":np.round(order_value,2),
        "refund_indicator":refund,
        "checkout_error_indicator":errors,
        "page_load_time_ms":np.round(load_time,1),
        "experiment_eligible":True
    })
