import pandas as pd
from src.data_generation import generate_experiment_data
from src.data_validation import validate_data
from src.metrics import analyze_conversion
from src.experiment_design import sample_size_two_proportions
from src.decision_engine import decide

def test_generator_reproducible():
    a=generate_experiment_data(1000,seed=7)
    b=generate_experiment_data(1000,seed=7)
    pd.testing.assert_frame_equal(a,b)

def test_conversion_metrics():
    df=generate_experiment_data(4000,baseline_rate=.10,treatment_effect=.04,seed=9)
    result=analyze_conversion(df)
    assert result["control_n"]+result["treatment_n"]==4000
    assert -1 <= result["absolute_lift"] <= 1
    assert 0 <= result["p_value"] <= 1

def test_sample_size():
    plan=sample_size_two_proportions(.10,.12)
    assert plan["n_per_arm"] > 0
    assert plan["total_n"] == plan["n_control"] + plan["n_treatment"]

def test_validation_detects_duplicate():
    df=generate_experiment_data(1000,seed=8)
    df=pd.concat([df,df.iloc[[0]]],ignore_index=True)
    result=validate_data(df)
    assert result["material_failure"]

def test_decision_blocks_invalid():
    conv={"control_n":500,"treatment_n":500,"ci_low":.01,"ci_high":.05,"p_value":.001}
    result=decide(conv,{"material_failure":True})
    assert result["outcome"]=="INVALID EXPERIMENT"
