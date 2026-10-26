"""Independent experiment data integrity checks."""
import pandas as pd
import numpy as np

REQUIRED = ["user_id","variant","assignment_timestamp","event_timestamp","device_type","country",
"acquisition_channel","is_new_customer","checkout_started","purchase_completed","order_value",
"refund_indicator","checkout_error_indicator","page_load_time_ms","experiment_eligible"]

def validate_data(df: pd.DataFrame, alpha=0.05, allocation=(0.5,0.5)):
    checks=[]
    def add(rule,status,severity,affected,explanation,action):
        checks.append({"rule":rule,"status":status,"severity":severity,"affected_records":int(affected),"explanation":explanation,"recommended_action":action})
    missing=[c for c in REQUIRED if c not in df.columns]
    add("Required schema","FAIL" if missing else "PASS","HIGH" if missing else "INFO",len(missing),"Missing columns: "+(", ".join(missing) if missing else "None"),"Add required columns before analysis." if missing else "No action required.")
    if missing:
        return {"checks":pd.DataFrame(checks),"material_failure":True,"raw_rows":len(df),"unique_users":df.get("user_id",pd.Series(dtype=str)).nunique()}
    add("Missing required values","WARN" if df[REQUIRED].isna().any().any() else "PASS","MEDIUM",int(df[REQUIRED].isna().any(axis=1).sum()),"Rows with at least one missing required value.","Investigate missingness; do not silently impute.")
    dup=int(df.user_id.duplicated(keep=False).sum())
    add("Duplicate user assignments","FAIL" if dup else "PASS","HIGH" if dup else "INFO",dup,"Repeated user_id values may violate one-row-per-user assignment.","Resolve assignment duplicates using a documented rule.")
    variants=set(df.variant.dropna().unique())
    bad=int((~df.variant.isin(["Control","Treatment"])).sum())
    add("Variant labels","FAIL" if bad or len(variants)<2 else "PASS","HIGH" if bad or len(variants)<2 else "INFO",bad,"Expected Control and Treatment variants.","Correct variant labels and verify both arms exist.")
    assign=pd.to_datetime(df.assignment_timestamp,errors="coerce",utc=True)
    event=pd.to_datetime(df.event_timestamp,errors="coerce",utc=True)
    badtime=int((assign.isna() | event.isna() | (event < assign)).sum())
    add("Timestamp validity","FAIL" if badtime else "PASS","HIGH" if badtime else "INFO",badtime,"Invalid timestamps or event preceding assignment.","Check event ingestion and timezone conversion.")
    inconsistent=0
    if "experiment_id" in df.columns:
        inconsistent=int(df.groupby("user_id").variant.nunique().gt(1).sum())
    add("Cross-variant assignment","FAIL" if inconsistent else "PASS","HIGH" if inconsistent else "INFO",inconsistent,"Users assigned to multiple variants.","Inspect randomization and identity stitching.")
    invalid_outcome=int(((df.purchase_completed.astype(bool)) & (pd.to_numeric(df.order_value,errors="coerce") < 0)).sum())
    add("Outcome consistency","FAIL" if invalid_outcome else "PASS","HIGH" if invalid_outcome else "INFO",invalid_outcome,"Purchases with negative order value.","Validate order/event joins and monetary values.")
    counts=df.variant.value_counts()
    observed=counts.reindex(["Control","Treatment"],fill_value=0).to_numpy()
    total=observed.sum()
    if total:
        expected=np.array(allocation)*total
        stat=float((((observed-expected)**2)/np.where(expected>0,expected,1)).sum())
        from scipy.stats import chi2
        p=float(chi2.sf(stat,1))
        srm=p < alpha
    else:
        p=1.0; srm=True
    add("Sample-ratio mismatch","FAIL" if srm else "PASS","HIGH" if srm else "INFO",int(total),"Allocation chi-square p-value: %.5f"%p,"Investigate allocation, eligibility, and logging; do not infer causality." if srm else "Continue reviewing other checks.")
    add("Minimum arm size","WARN" if min(observed)<100 else "PASS","MEDIUM" if min(observed)<100 else "INFO",int(min(observed)),"Demo threshold is 100 users per arm.","Collect more data before interpreting small samples.")
    material=any(c["status"]=="FAIL" and c["severity"]=="HIGH" for c in checks)
    return {"checks":pd.DataFrame(checks),"material_failure":material,"raw_rows":len(df),"unique_users":df.user_id.nunique()}
