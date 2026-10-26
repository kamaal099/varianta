"""Transparent decision rules for decision support, not release authorization."""
def decide(conversion, validation, alpha=0.05, min_users=100, guardrails_ok=True):
    if validation.get("material_failure",True):
        return {"outcome":"INVALID EXPERIMENT","rationale":"Material data-integrity failures prevent reliable causal inference.","next_action":"Fix assignment, schema, or event-quality issues and rerun validation."}
    if min(conversion["control_n"],conversion["treatment_n"]) < min_users:
        return {"outcome":"INCONCLUSIVE","rationale":"At least one arm is below the configured minimum sample threshold.","next_action":"Continue collecting data according to the prespecified protocol."}
    if not guardrails_ok:
        return {"outcome":"DO NOT LAUNCH","rationale":"A configured guardrail is unacceptable.","next_action":"Investigate harm and redesign the treatment before reconsidering."}
    if conversion["ci_low"] > 0 and conversion["p_value"] < alpha:
        return {"outcome":"LAUNCH CANDIDATE","rationale":"The primary conversion difference is positive with a confidence interval above zero and passes the selected significance threshold. Guardrails still require review.","next_action":"Review guardrails, duration, practical significance, and implementation risks with the product owner."}
    if conversion["ci_high"] < 0 and conversion["p_value"] < alpha:
        return {"outcome":"DO NOT LAUNCH","rationale":"Evidence indicates the treatment reduces conversion.","next_action":"Reject or revise the treatment and investigate the mechanism."}
    return {"outcome":"INCONCLUSIVE","rationale":"The available evidence does not establish the prespecified success or harm criterion. Nonsignificance is not proof of no effect.","next_action":"Collect more evidence if the protocol allows, or retain control and document uncertainty."}
