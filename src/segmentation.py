"""Prespecified segment summaries and Benjamini-Hochberg correction."""
import pandas as pd
from .metrics import analyze_conversion

def segment_conversion(df, dimension, alpha=0.05, min_n=100):
    rows=[]
    for label, part in df.groupby(dimension, dropna=False):
        if part.variant.nunique()<2:
            continue
        result=analyze_conversion(part,alpha=alpha)
        rows.append({"segment":str(label),"dimension":dimension,"n_total":len(part),
        "control_n":result["control_n"],"treatment_n":result["treatment_n"],
        "control_rate":result["control_rate"],"treatment_rate":result["treatment_rate"],
        "absolute_lift":result["absolute_lift"],"relative_lift":result["relative_lift"],
        "ci_low":result["ci_low"],"ci_high":result["ci_high"],"p_value":result["p_value"],
        "sparse":len(part)<min_n})
    out=pd.DataFrame(rows)
    if not out.empty:
        from statsmodels.stats.multitest import multipletests
        out["p_adjusted_bh"]=multipletests(out.p_value,method="fdr_bh")[1]
        out["exploratory_warning"]="Exploratory; interpret with multiplicity and sample-size caution"
    return out
