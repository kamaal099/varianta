"""Business impact projections based on the observed conversion difference."""
def calculate_business_impact(conversion, eligible_users, contribution_margin=0.0, average_order_value=None):
    n=float(eligible_users)
    delta=float(conversion["absolute_lift"])
    aov=float(average_order_value) if average_order_value is not None else 0.0
    conversions=delta*n
    revenue=conversions*aov
    return {"eligible_users":int(n),"absolute_conversion_lift":delta,"incremental_conversions":conversions,
    "assumed_average_order_value":aov,"incremental_revenue":revenue,
    "contribution_margin_per_order":float(contribution_margin),
    "contribution_impact":conversions*float(contribution_margin),
    "interpretation":"Projection, not realized outcome. Uses observed lift; uncertainty is represented by the conversion CI and is not a forecast guarantee."}
