"""JSON-serializable decision report."""
from datetime import datetime, timezone

def build_report(name, source, validation, conversion, decision, impact):
    return {"report_version":"1.0","generated_at":datetime.now(timezone.utc).isoformat(),
    "experiment_name":name,"data_source":source,"synthetic_data_warning":"Synthetic demo results are not real company outcomes.",
    "validation":{"raw_rows":validation["raw_rows"],"unique_users":validation["unique_users"],"material_failure":validation["material_failure"],"checks":validation["checks"].to_dict(orient="records")},
    "primary_metric":conversion,"decision":decision,"business_impact":impact,
    "limitations":["Fixed-horizon inference assumes the analysis plan was followed.","This demo does not implement valid sequential testing.","Guardrail values are shown but configurable non-inferiority testing is not implemented.","Segment results are exploratory and corrected p-values should be used.","Business impact is a projection, not realized revenue."]}
