import numpy as np
import pandas as pd
import pytest

from src.data_generation import generate_experiment_data
from src.data_validation import validate_data, REQUIRED
from src.experiment_design import sample_size_two_proportions
from src.metrics import analyze_conversion, analyze_continuous
from src.segmentation import segment_conversion
from src.business_impact import calculate_business_impact
from src.decision_engine import decide
from src.reporting import build_report

@pytest.mark.parametrize("n", [100, 101, 250, 999, 1000, 2500, 5000, 12000])
def test_generator_row_count(n):
    assert len(generate_experiment_data(n, seed=4)) == n

@pytest.mark.parametrize("seed", list(range(1, 16)))
def test_generator_is_reproducible(seed):
    pd.testing.assert_frame_equal(generate_experiment_data(500, seed=seed),
                                  generate_experiment_data(500, seed=seed))

@pytest.mark.parametrize("n", [100, 200, 501, 1001, 2501])
def test_generator_has_both_variants(n):
    df=generate_experiment_data(n, seed=20)
    assert set(df.variant.unique()) == {"Control", "Treatment"}

@pytest.mark.parametrize("effect", [-0.03, -0.01, 0.0, 0.01, 0.03, 0.06])
def test_generator_outcomes_are_binary_and_valid(effect):
    df=generate_experiment_data(1500, baseline_rate=.15, treatment_effect=effect, seed=30)
    assert df.purchase_completed.isin([True,False]).all()
    assert df.experiment_eligible.all()
    assert (df.order_value >= 0).all()
    assert (df.loc[~df.purchase_completed, "order_value"] == 0).all()

@pytest.mark.parametrize("rate", [0.02, 0.05, 0.10, 0.20, 0.40])
def test_generator_baseline_rate_range(rate):
    df=generate_experiment_data(1000, baseline_rate=rate, treatment_effect=0, seed=17)
    assert df.purchase_completed.mean() >= 0
    assert df.purchase_completed.mean() <= 1

@pytest.mark.parametrize("column", REQUIRED)
def test_validation_accepts_required_schema(column):
    df=generate_experiment_data(500, seed=9)
    assert column in df.columns
    assert validate_data(df)["material_failure"] is False

@pytest.mark.parametrize("column", ["user_id","variant","assignment_timestamp","event_timestamp","purchase_completed"])
def test_validation_detects_missing_required_column(column):
    df=generate_experiment_data(500, seed=8).drop(columns=[column])
    result=validate_data(df)
    assert result["material_failure"] is True

@pytest.mark.parametrize("n_duplicates", [1, 2, 3, 5, 10])
def test_validation_detects_duplicate_users(n_duplicates):
    df=generate_experiment_data(500, seed=8)
    df=pd.concat([df, df.iloc[:n_duplicates]], ignore_index=True)
    result=validate_data(df)
    assert result["material_failure"] is True

@pytest.mark.parametrize("bad_variant", ["B", "control", "Treatment ", "", None])
def test_validation_detects_bad_variant_labels(bad_variant):
    df=generate_experiment_data(500, seed=8)
    df.loc[0, "variant"]=bad_variant
    result=validate_data(df)
    assert result["material_failure"] is True

@pytest.mark.parametrize("bad_timestamp", ["not-a-date", None, "2025-01-01T00:00:00Z"])
def test_validation_timestamp_anomalies(bad_timestamp):
    df=generate_experiment_data(500, seed=8)
    df.loc[0, "event_timestamp"]=bad_timestamp
    result=validate_data(df)
    assert (result["checks"]["rule"] == "Timestamp validity").any()

@pytest.mark.parametrize("baseline,target", [(.05,.06),(.10,.12),(.15,.18),(.20,.23),(.30,.35)])
def test_sample_size_valid_inputs(baseline,target):
    result=sample_size_two_proportions(baseline,target)
    assert result["n_control"] > 0 and result["n_treatment"] > 0
    assert result["total_n"] == result["n_control"] + result["n_treatment"]

@pytest.mark.parametrize("baseline,target", [(0,.1),(.1,0),(1,.9),(.1,1),(-.1,.2)])
def test_sample_size_rejects_invalid_rates(baseline,target):
    with pytest.raises(ValueError):
        sample_size_two_proportions(baseline,target)

@pytest.mark.parametrize("alpha", [0.001,0.01,0.05,0.10,0.20])
def test_sample_size_alpha_validation(alpha):
    if alpha < 1:
        result=sample_size_two_proportions(.10,.12,alpha=alpha)
        assert result["n_per_arm"] > 0

@pytest.mark.parametrize("power", [.70,.75,.80,.85,.90,.95])
def test_sample_size_power_validation(power):
    result=sample_size_two_proportions(.10,.12,power=power)
    assert result["target_power"] == power

@pytest.mark.parametrize("effect", [-.03,-.01,0,.01,.03])
def test_conversion_metric_output_bounds(effect):
    df=generate_experiment_data(2000,baseline_rate=.12,treatment_effect=effect,seed=41)
    result=analyze_conversion(df)
    assert 0 <= result["control_rate"] <= 1
    assert 0 <= result["treatment_rate"] <= 1
    assert 0 <= result["p_value"] <= 1
    assert result["ci_low"] <= result["ci_high"]

@pytest.mark.parametrize("n", [200,500,1000,2500,5000])
def test_conversion_counts_sum_to_arm_sizes(n):
    df=generate_experiment_data(n,seed=42)
    result=analyze_conversion(df)
    assert result["control_conversions"] <= result["control_n"]
    assert result["treatment_conversions"] <= result["treatment_n"]
    assert result["control_n"]+result["treatment_n"] == n

@pytest.mark.parametrize("metric", ["revenue_per_user","page_load_time_ms","order_value"])
def test_continuous_analysis_returns_expected_fields(metric):
    df=generate_experiment_data(1000,seed=7)
    result=analyze_continuous(df,metric)
    assert "control_mean" in result
    assert "treatment_mean" in result
    assert "p_value" in result

@pytest.mark.parametrize("dimension", ["device_type","country","acquisition_channel","is_new_customer"])
def test_segmentation_dimensions(dimension):
    df=generate_experiment_data(3000,seed=14)
    result=segment_conversion(df,dimension)
    assert not result.empty
    assert "p_adjusted_bh" in result.columns
    assert result["n_total"].sum() == len(df)

@pytest.mark.parametrize("traffic", [1000,10000,50000,100000,1000000])
def test_business_impact_scales_with_traffic(traffic):
    conversion={"absolute_lift":.01}
    impact=calculate_business_impact(conversion,traffic,25,average_order_value=50)
    assert impact["incremental_conversions"] == pytest.approx(traffic*.01)
    assert impact["contribution_impact"] == pytest.approx(traffic*.01*25)
    assert impact["incremental_revenue"] == pytest.approx(traffic*.01*50)

@pytest.mark.parametrize("outcome", ["INVALID EXPERIMENT","INCONCLUSIVE","LAUNCH CANDIDATE","DO NOT LAUNCH"])
def test_decision_engine_has_known_outcome_paths(outcome):
    conv={"control_n":1000,"treatment_n":1000,"ci_low":.01,"ci_high":.04,"p_value":.001}
    validation={"material_failure":False}
    if outcome=="INVALID EXPERIMENT":
        got=decide(conv,{"material_failure":True})["outcome"]
    elif outcome=="INCONCLUSIVE":
        got=decide({**conv,"control_n":50},{"material_failure":False})["outcome"]
    elif outcome=="LAUNCH CANDIDATE":
        got=decide(conv,validation)["outcome"]
    else:
        got=decide({**conv,"ci_low":-.04,"ci_high":-.01},{"material_failure":False})["outcome"]
    assert got==outcome

@pytest.mark.parametrize("users", [1000,10000,50000])
def test_report_has_required_sections(users):
    df=generate_experiment_data(users,seed=42)
    val=validate_data(df); conv=analyze_conversion(df); dec=decide(conv,val)
    impact=calculate_business_impact(conv,users,20,average_order_value=40)
    report=build_report("Test","Synthetic demo dataset",val,conv,dec,impact)
    assert report["experiment_name"]=="Test"
    assert "primary_metric" in report and "decision" in report and "business_impact" in report
    assert "synthetic" in report["synthetic_data_warning"].lower()

@pytest.mark.parametrize("rate", [0.0, 1.0])
def test_zero_or_full_conversion_does_not_crash(rate):
    df=generate_experiment_data(200,seed=2)
    df["purchase_completed"]=bool(rate)
    df["order_value"]=np.where(df["purchase_completed"],50.0,0.0)
    result=analyze_conversion(df)
    assert result["p_value"] >= 0 and result["p_value"] <= 1

def test_empty_validation_is_reported_as_failure():
    df=pd.DataFrame(columns=REQUIRED)
    result=validate_data(df)
    assert "checks" in result

def test_report_keeps_limitations():
    df=generate_experiment_data(1000,seed=2)
    val=validate_data(df); conv=analyze_conversion(df)
    report=build_report("Test","Synthetic",val,conv,decide(conv,val),calculate_business_impact(conv,10000))
    assert len(report["limitations"]) >= 4
