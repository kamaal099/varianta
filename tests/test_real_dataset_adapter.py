import pandas as pd
import pytest
from src.real_dataset_adapter import adapt_ecommerce_ab_dataset


def sample_raw():
    return pd.DataFrame({
        "user_id": [1, 2, 3, 4, 4, 5, 6],
        "timestamp": ["2024-01-01T10:00:00Z", "2024-01-02T10:00:00Z", "2024-01-03T10:00:00Z",
                      "2024-01-04T10:00:00Z", "2024-01-04T11:00:00Z", "not-a-date", "2024-01-06T10:00:00Z"],
        "group": ["control", "treatment", "control", "treatment", "treatment", "control", "bogus"],
        "landing_page": ["old_page", "new_page", "new_page", "new_page", "new_page", "old_page", "old_page"],
        "converted": [0, 1, 0, 1, 0, 1, 0],
    })


def test_adapter_normalizes_and_tracks_cleaning():
    adapted, audit = adapt_ecommerce_ab_dataset(sample_raw())
    assert set(adapted.variant) == {"Control", "Treatment"}
    assert adapted.user_id.is_unique
    assert set(adapted.purchase_completed.unique()).issubset({True, False})
    assert audit["source_rows"] == 7
    assert audit["group_page_mismatch_rows_removed"] >= 2
    assert audit["duplicate_user_rows_removed"] == 1
    assert audit["revenue_available"] is False


def test_adapter_rejects_missing_schema():
    with pytest.raises(ValueError, match="requires columns"):
        adapt_ecommerce_ab_dataset(pd.DataFrame({"user_id": [1], "converted": [1]}))


def test_adapter_does_not_fabricate_revenue():
    adapted, audit = adapt_ecommerce_ab_dataset(sample_raw())
    assert (adapted.order_value == 0).all()
    assert audit["revenue_available"] is False


def test_adapter_keeps_only_binary_outcomes():
    raw = sample_raw()
    raw.loc[0, "converted"] = 2
    adapted, audit = adapt_ecommerce_ab_dataset(raw)
    assert audit["invalid_outcome_rows_removed"] == 1
    assert set(adapted.converted.unique()).issubset({0, 1})
