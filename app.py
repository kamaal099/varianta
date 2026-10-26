import json
from datetime import datetime, timezone

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.data_generation import generate_experiment_data
from src.data_validation import validate_data
from src.experiment_design import sample_size_two_proportions
from src.metrics import analyze_conversion, analyze_continuous
from src.segmentation import segment_conversion
from src.business_impact import calculate_business_impact
from src.decision_engine import decide
from src.reporting import build_report
from src.database import init_db, save_analysis
from src.real_dataset_adapter import PUBLIC_AB_DATA_URL, adapt_ecommerce_ab_dataset


# ---------------------------------------------------------------------------
# Page configuration and design system
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Varianta | Experiment Intelligence",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap');

    :root {
        --ink: #172033;
        --muted: #667085;
        --line: #e7eaf1;
        --surface: #ffffff;
        --canvas: #f6f8fc;
        --accent: #6257e8;
        --accent-soft: #efedff;
        --teal: #0d9488;
    }
    html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
    .stApp { background: var(--canvas); color: var(--ink); }
    [data-testid="stHeader"] { background: rgba(246,248,252,.88); }
    [data-testid="stToolbar"] { right: 1.5rem; }
    .block-container { max-width: 1600px; padding: 1.5rem 2.1rem 3rem; }
    h1, h2, h3 { font-family: 'Manrope', sans-serif !important; color: var(--ink); letter-spacing: -0.035em; }
    h1 { font-size: 2.05rem !important; font-weight: 800 !important; }
    h2 { font-size: 1.35rem !important; font-weight: 750 !important; }
    h3 { font-size: 1.02rem !important; font-weight: 700 !important; }
    p, label, .stCaption { color: var(--muted); }
    [data-testid="stSidebar"] { background: #fff; border-right: 1px solid var(--line); }
    [data-testid="stSidebar"] > div:first-child { padding-top: 1.1rem; }
    [data-testid="stMetric"] {
        background: var(--surface); border: 1px solid var(--line);
        border-radius: 16px; padding: 18px 20px; box-shadow: 0 2px 7px rgba(22,34,66,.025);
    }
    [data-testid="stMetricLabel"] { color: #68738a; font-size: .82rem; font-weight: 600; }
    [data-testid="stMetricValue"] { color: var(--ink); font-family: 'Manrope', sans-serif; font-weight: 800; }
    [data-testid="stTabs"] [role="tablist"] {
        gap: 5px; border-bottom: 1px solid var(--line); padding-bottom: 7px;
    }
    [data-testid="stTabs"] button[role="tab"] {
        border-radius: 10px; padding: 9px 14px; color: #667085; font-weight: 650;
    }
    [data-testid="stTabs"] button[aria-selected="true"] {
        background: var(--accent-soft); color: var(--accent);
    }
    div.stButton > button, div.stDownloadButton > button {
        border-radius: 10px; font-weight: 650; border: 1px solid #dedff7;
    }
    div.stButton > button[kind="primary"] { background: var(--accent); border-color: var(--accent); }
    div[data-testid="stAlert"] { border-radius: 12px; }
    div[data-testid="stDataFrame"] { border: 1px solid var(--line); border-radius: 12px; overflow: hidden; }
    .brand-row { display:flex; align-items:center; gap:12px; margin: 0 0 1.2rem; }
    .brand-mark {
        width:42px;height:42px;border-radius:13px;display:flex;align-items:center;justify-content:center;
        color:white;background:linear-gradient(135deg,#7468ff,#4d46c7);font-size:22px;
        box-shadow:0 7px 18px rgba(98,87,232,.22);
    }
    .brand-name { font-family:'Manrope',sans-serif;font-weight:800;font-size:1.15rem;color:var(--ink);line-height:1.15; }
    .brand-tag { color:#8a93a6;font-size:.72rem;letter-spacing:.09em;text-transform:uppercase;margin-top:4px; }
    .hero {
        background: linear-gradient(115deg,#191f3b 0%,#29275a 56%,#4d46b4 100%);
        border-radius: 22px; padding: 27px 30px; color: white; margin: 0 0 22px;
        position: relative; overflow: hidden;
    }
    .hero:after {
        content:""; position:absolute; width:270px;height:270px;border-radius:50%;
        border:1px solid rgba(255,255,255,.12); right:-60px;top:-145px;
        box-shadow:0 0 0 35px rgba(255,255,255,.025),0 0 0 75px rgba(255,255,255,.02);
    }
    .hero-eyebrow { font-size:.72rem;text-transform:uppercase;letter-spacing:.15em;color:#c8c5ff;font-weight:700; }
    .hero-title { font-family:'Manrope',sans-serif;font-size:1.8rem;font-weight:800;letter-spacing:-.04em;color:white;margin:7px 0 5px; }
    .hero-copy { color:#d8d9ee;font-size:.92rem;max-width:720px;line-height:1.55; }
    .hero-pill { display:inline-block;margin-top:14px;padding:6px 10px;border-radius:100px;
        background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.15);font-size:.75rem;color:#f1f0ff; }
    .section-head { display:flex;align-items:center;justify-content:space-between;gap:10px;margin:8px 0 14px; }
    .section-kicker { color:#8a93a6;font-size:.72rem;font-weight:700;letter-spacing:.12em;text-transform:uppercase; }
    .panel {
        background:white;border:1px solid var(--line);border-radius:16px;padding:18px 20px;
        box-shadow:0 2px 7px rgba(22,34,66,.02); margin-bottom:12px;
    }
    .panel-title { color:var(--ink);font-weight:750;font-family:'Manrope',sans-serif;margin-bottom:5px; }
    .panel-sub { color:var(--muted);font-size:.85rem;line-height:1.5; }
    .status-chip { display:inline-block;border-radius:100px;padding:5px 10px;font-size:.73rem;font-weight:700; }
    .chip-purple { background:#efedff;color:#5b50d6; }
    .chip-green { background:#e8f8f2;color:#087f5b; }
    .chip-amber { background:#fff4dd;color:#9a6700; }
    .footer-note { color:#98a0b0;font-size:.75rem;border-top:1px solid var(--line);padding-top:16px;margin-top:28px; }
    </style>
    """,
    unsafe_allow_html=True,
)

init_db()

# ---------------------------------------------------------------------------
# Sidebar controls
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown(
        """
        <div class="brand-row">
          <div class="brand-mark">✳</div>
          <div><div class="brand-name">Varianta</div>
          <div class="brand-tag">Experiment intelligence</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("### Experiment setup")
    st.caption("Configure a demo experiment or analyse your own dataset.")

    name = st.text_input("Experiment name", "Redesigned checkout")
    data_mode = st.radio("Data source", ["Generate demo data", "Public e-commerce A/B dataset", "Upload CSV"], horizontal=False)
    n_users = st.slider("Eligible users", 1_000, 50_000, 12_000, 1_000, disabled=(data_mode != "Generate demo data"))
    baseline = st.slider("Baseline conversion", 0.02, 0.40, 0.12, 0.01, disabled=(data_mode != "Generate demo data"))
    effect = st.slider("Treatment effect (absolute)", -0.04, 0.06, 0.015, 0.005, disabled=(data_mode != "Generate demo data"))
    seed = st.number_input("Random seed", min_value=1, value=42, step=1, disabled=(data_mode != "Generate demo data"))
    upload = st.file_uploader("Upload experiment CSV", type=["csv"], disabled=(data_mode != "Upload CSV"))
    st.caption("Public dataset downloads from GitHub when selected; internet access is required.")

    st.markdown("---")
    st.markdown("### Statistical settings")
    alpha = st.selectbox("Significance level (α)", [0.01, 0.05, 0.10], index=1)
    power = st.slider("Target statistical power", 0.70, 0.95, 0.80, 0.05)
    mde = st.slider("Minimum detectable effect", 0.005, 0.08, 0.02, 0.005)

    st.markdown("---")
    st.markdown("### Business assumptions")
    traffic = st.number_input("Eligible users per day", min_value=100, value=3_000, step=100)
    business_traffic = st.number_input("Projection population", min_value=1_000, value=100_000, step=1_000)
    margin = st.number_input("Contribution margin per order ($)", min_value=0.0, value=35.0, step=5.0)

    run_label = ("CSV selected" if upload is not None else "Waiting for CSV…") if data_mode == "Upload CSV" else ("Public real-world dataset" if data_mode == "Public e-commerce A/B dataset" else "Synthetic demo")
    st.markdown("---")
    st.markdown(f'<span class="status-chip chip-purple">{run_label}</span>', unsafe_allow_html=True)
    st.caption("Synthetic values are illustrative and must not be represented as company results.")

# ---------------------------------------------------------------------------
# Load and validate source
# ---------------------------------------------------------------------------
real_data_audit = None
revenue_available = True
if data_mode == "Upload CSV":
    if upload is None:
        st.markdown(
            """
            <div class="hero">
              <div class="hero-eyebrow">Experiment workspace</div>
              <div class="hero-title">Make better product decisions.</div>
              <div class="hero-copy">Upload an experiment-level CSV to inspect data quality, estimate treatment effects,
              explore segments and translate results into business impact.</div>
              <span class="hero-pill">A/B testing · Statistical analysis · Decision support</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.info("Choose a CSV in the sidebar to begin. Varianta accepts its canonical schema or the common e-commerce A/B schema (user_id, timestamp, group, landing_page, converted).")
        st.stop()
    try:
        raw_upload = pd.read_csv(upload)
        cols = {str(c).strip().lower() for c in raw_upload.columns}
        if {"user_id", "timestamp", "group", "landing_page", "converted"}.issubset(cols):
            df, real_data_audit = adapt_ecommerce_ab_dataset(raw_upload)
            revenue_available = False
            source_label = "Uploaded public-style e-commerce A/B dataset"
        else:
            df = raw_upload
            source_label = "Uploaded dataset (user supplied)"
    except Exception as exc:
        st.error(f"Unable to read or adapt the uploaded CSV: {exc}")
        st.stop()
elif data_mode == "Public e-commerce A/B dataset":
    try:
        with st.spinner("Downloading and cleaning the public e-commerce A/B dataset…"):
            raw_public = pd.read_csv(PUBLIC_AB_DATA_URL)
            df, real_data_audit = adapt_ecommerce_ab_dataset(raw_public)
        revenue_available = False
        source_label = "Public educational e-commerce A/B dataset (GitHub mirror of Udacity/Kaggle dataset)"
    except Exception as exc:
        st.error(f"Could not download the public dataset. Check your internet connection or use Upload CSV. Details: {exc}")
        st.stop()
else:
    df = generate_experiment_data(
        n_users=n_users,
        baseline_rate=baseline,
        treatment_effect=effect,
        seed=int(seed),
    )
    source_label = "Synthetic demo dataset"

required = [
    "user_id", "variant", "assignment_timestamp", "event_timestamp", "device_type",
    "country", "acquisition_channel", "is_new_customer", "checkout_started",
    "purchase_completed", "order_value", "refund_indicator", "checkout_error_indicator",
    "page_load_time_ms", "experiment_eligible",
]
missing = [col for col in required if col not in df.columns]
if missing:
    st.error("The CSV is missing required columns: " + ", ".join(missing))
    st.caption("See docs/data_dictionary.md for the expected schema.")
    st.stop()

validation = validate_data(df, alpha=alpha)
eligible = df[df["experiment_eligible"].astype(bool)].copy()
eligible = eligible.sort_values("assignment_timestamp").drop_duplicates("user_id", keep="first")
control = eligible[eligible.variant == "Control"]
treatment = eligible[eligible.variant == "Treatment"]
if control.empty or treatment.empty:
    st.error("Both Control and Treatment must contain eligible users. Check the variant labels and eligibility column.")
    st.stop()

conv = analyze_conversion(eligible, alpha=alpha)
decision = decide(conv, validation, alpha=alpha, min_users=100)
purchases = eligible["purchase_completed"].astype(bool)
observed_aov = float(eligible.loc[purchases, "order_value"].mean()) if purchases.any() else 0.0
impact = calculate_business_impact(conv, business_traffic, margin, average_order_value=observed_aov)
impact_for_report = impact if revenue_available else {
    "eligible_users": impact["eligible_users"],
    "absolute_conversion_lift": impact["absolute_conversion_lift"],
    "incremental_conversions": impact["incremental_conversions"],
    "interpretation": "Conversion-only projection. Revenue and contribution cannot be estimated because this dataset has no order-value or margin fields.",
}
report = build_report(name, source_label, validation, conv, decision, impact_for_report)
save_analysis(name, source_label, validation, conv, decision, report)

# ---------------------------------------------------------------------------
# App header
# ---------------------------------------------------------------------------
now_label = datetime.now().strftime("%d %b %Y")
st.markdown(
    f"""
    <div class="hero">
      <div class="hero-eyebrow">Experiment workspace · {now_label}</div>
      <div class="hero-title">{name if name else "Untitled experiment"}</div>
      <div class="hero-copy">Measure the impact of product changes with transparent statistical evidence,
      data-quality checks and business-oriented recommendations.</div>
      <span class="hero-pill">● {source_label}</span>
    </div>
    """,
    unsafe_allow_html=True,
)

if source_label.startswith("Synthetic"):
    st.info("Demo mode: all observations are simulated. Use uploaded or public experiment data for real-data validation.")
elif real_data_audit is not None:
    with st.expander("Dataset provenance & cleaning audit", expanded=True):
        source_urls = [
            "https://github.com/beery4010/Analyze-AB-Test-Results",
            "https://www.kaggle.com/datasets/zhangluyuan/ab-testing",
        ]
        source_rows = int(real_data_audit.get("source_rows", len(df)))
        retained_rows = int(real_data_audit.get("analysis_rows", len(df)))
        excluded_rows = max(source_rows - retained_rows, 0)
        mismatch_rows = int(real_data_audit.get("group_page_mismatch_rows_removed", 0))
        duplicate_rows = int(real_data_audit.get("duplicate_user_rows_removed", 0))
        invalid_outcomes = int(real_data_audit.get("invalid_outcome_rows_removed", 0))
        invalid_timestamps = int(real_data_audit.get("invalid_timestamp_rows_removed", 0))
        audit_rows = [
            {"Audit item": "Original source rows", "Count / value": source_rows, "Explanation": "Rows read from the source CSV before cleaning."},
            {"Audit item": "Group/page mismatches excluded", "Count / value": mismatch_rows, "Explanation": "Assignment group did not match the landing page."},
            {"Audit item": "Duplicate user rows excluded", "Count / value": duplicate_rows, "Explanation": "Repeated user IDs removed after chronological sorting; earliest valid row retained."},
            {"Audit item": "Invalid outcomes excluded", "Count / value": invalid_outcomes, "Explanation": "Outcome was not binary or user ID was missing."},
            {"Audit item": "Invalid timestamps excluded", "Count / value": invalid_timestamps, "Explanation": "Timestamp could not be parsed."},
            {"Audit item": "Total rows excluded", "Count / value": excluded_rows, "Explanation": "Original rows minus retained analysis rows; exclusion categories are sequential cleaning stages."},
            {"Audit item": "Retained analysis rows", "Count / value": retained_rows, "Explanation": "User-level rows passed the dataset adapter's cleaning rules."},
            {"Audit item": "Control users", "Count / value": int(real_data_audit.get("control_users", 0)), "Explanation": "Retained users assigned to Control."},
            {"Audit item": "Treatment users", "Count / value": int(real_data_audit.get("treatment_users", 0)), "Explanation": "Retained users assigned to Treatment."},
            {"Audit item": "Conversion events", "Count / value": int(real_data_audit.get("conversion_events", 0)), "Explanation": "Sum of the binary conversion outcome."},
            {"Audit item": "Revenue available", "Count / value": bool(real_data_audit.get("revenue_available", False)), "Explanation": "This source does not provide order value or revenue."},
        ]
        st.markdown("**Source:** public educational e-commerce landing-page A/B test mirrored on GitHub. It is not verified production data. Cleaning is transparent; categories reflect sequential cleaning stages and should not be added together as if every row had only one possible issue.")
        a1, a2, a3 = st.columns(3)
        a1.metric("Original rows", f"{source_rows:,}")
        a2.metric("Excluded rows", f"{excluded_rows:,}")
        a3.metric("Retained rows", f"{retained_rows:,}")
        st.dataframe(pd.DataFrame(audit_rows), use_container_width=True, hide_index=True)
        st.caption("Source references: " + " · ".join(source_urls) + ". Only conversion is measured; revenue, refunds, checkout errors and page-performance guardrails are unavailable.")
        audit_payload = {
            "audit_schema_version": "1.0",
            "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "experiment_name": name,
            "source_label": source_label,
            "source_reference": source_urls,
            "dataset_type": "public educational e-commerce landing-page A/B dataset",
            "production_data_verified": False,
            "original_rows": source_rows,
            "excluded_rows_total": excluded_rows,
            "retained_rows": retained_rows,
            "retained_row_percentage": round((retained_rows / source_rows * 100), 4) if source_rows else None,
            "exclusion_reasons": {
                "group_page_mismatch_rows_removed": mismatch_rows,
                "duplicate_user_rows_removed": duplicate_rows,
                "invalid_outcome_rows_removed": invalid_outcomes,
                "invalid_timestamp_rows_removed": invalid_timestamps,
            },
            "cleaning_audit_raw": real_data_audit,
            "analysis_population": {
                "control_users": int(real_data_audit.get("control_users", 0)),
                "treatment_users": int(real_data_audit.get("treatment_users", 0)),
                "conversion_events": int(real_data_audit.get("conversion_events", 0)),
            },
            "revenue_available": bool(real_data_audit.get("revenue_available", False)),
            "limitations": [
                "Educational dataset; not verified production experiment data.",
                "Only a binary conversion outcome is measured.",
                "Revenue, order value, refunds, checkout errors and page-performance guardrails are unavailable.",
                "Rows are removed in sequential cleaning stages; category counts are not necessarily mutually exclusive across stages.",
            ],
        }
        exp_a, exp_b = st.columns(2)
        with exp_a:
            st.download_button("Download provenance audit (JSON)", json.dumps(audit_payload, indent=2, default=str), file_name="varianta_provenance_audit.json", mime="application/json", use_container_width=True)
        with exp_b:
            st.download_button("Download cleaning audit (CSV)", pd.DataFrame(audit_rows).to_csv(index=False), file_name="varianta_cleaning_audit.csv", mime="text/csv", use_container_width=True)

# ---------------------------------------------------------------------------
# Navigation
# ---------------------------------------------------------------------------
tabs = st.tabs([
    "Overview", "Data quality", "Experiment design", "Statistical results",
    "Segments", "Business impact", "Decision & exports", "Data explorer"
])

# Overview
with tabs[0]:
    st.markdown('<div class="section-kicker">Executive snapshot</div>', unsafe_allow_html=True)
    st.markdown("## Performance at a glance")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Control conversion", f"{conv['control_rate']:.2%}", help="Purchases divided by eligible randomized users in Control.")
    c2.metric("Treatment conversion", f"{conv['treatment_rate']:.2%}", help="Purchases divided by eligible randomized users in Treatment.")
    c3.metric("Absolute lift", f"{conv['absolute_lift']:+.2%}", help="Treatment conversion minus Control conversion.")
    c4.metric("Relative lift", f"{conv['relative_lift']:+.1%}" if pd.notna(conv["relative_lift"]) else "N/A")

    left, right = st.columns([1.35, 1])
    with left:
        st.markdown('<div class="panel"><div class="panel-title">Conversion by variant</div><div class="panel-sub">Primary metric · purchase conversion per eligible randomized user</div></div>', unsafe_allow_html=True)
        from scipy.stats import norm as _norm
        def _wilson_interval(successes, total, confidence=0.95):
            if total <= 0: return (float("nan"), float("nan"))
            z = float(_norm.ppf(1 - (1-confidence)/2)); p = successes / total
            den = 1 + z*z/total
            center = (p + z*z/(2*total)) / den
            half = z * ((p*(1-p)/total + z*z/(4*total*total)) ** 0.5) / den
            return max(0.0, center-half), min(1.0, center+half)
        c_lo, c_hi = _wilson_interval(conv["control_conversions"], conv["control_n"])
        t_lo, t_hi = _wilson_interval(conv["treatment_conversions"], conv["treatment_n"])
        chart_df = pd.DataFrame({"Variant": ["Control", "Treatment"], "Conversion rate": [conv["control_rate"], conv["treatment_rate"]], "Users": [conv["control_n"], conv["treatment_n"]], "Lower": [c_lo, t_lo], "Upper": [c_hi, t_hi]})
        chart_df["Error minus"] = chart_df["Conversion rate"] - chart_df["Lower"]
        chart_df["Error plus"] = chart_df["Upper"] - chart_df["Conversion rate"]
        fig = px.bar(chart_df, x="Variant", y="Conversion rate", text=chart_df["Conversion rate"].map(lambda x: f"{x:.2%}"), color="Variant", color_discrete_map={"Control": "#a5abc0", "Treatment": "#6257e8"}, custom_data=["Users", "Lower", "Upper"])
        fig.update_traces(textposition="outside", cliponaxis=False, error_y=dict(type="data", symmetric=False, array=chart_df["Error plus"], arrayminus=chart_df["Error minus"], visible=True, color="#30384b", thickness=1.5, width=5), hovertemplate="%{x}<br>Conversion: %{y:.2%}<br>Users: %{customdata[0]:,.0f}<br>95% Wilson CI: [%{customdata[1]:.2%}, %{customdata[2]:.2%}]<extra></extra>")
        fig.update_layout(showlegend=False, height=365, margin=dict(l=10,r=15,t=25,b=10), yaxis=dict(tickformat=".0%", title="", gridcolor="#edf0f6", rangemode="tozero"), xaxis_title="", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#667085")
        st.plotly_chart(fig, use_container_width=True)
        st.caption(f"Bars show conversion rates; whiskers show 95% Wilson confidence intervals for each arm. Treatment-effect CI: [{conv['ci_low']:+.2%}, {conv['ci_high']:+.2%}].")
    with right:
        st.markdown('<div class="panel"><div class="panel-title">Decision status</div><div class="panel-sub">Based on the selected significance threshold and data checks</div></div>', unsafe_allow_html=True)
        outcome = str(decision.get("outcome", "Review required"))
        if validation.get("material_failure"):
            st.markdown('<span class="status-chip chip-amber">Integrity review required</span>', unsafe_allow_html=True)
        elif "ship" in outcome.lower() or "roll" in outcome.lower() or "positive" in outcome.lower():
            st.markdown('<span class="status-chip chip-green">Positive signal</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="status-chip chip-purple">Evidence review</span>', unsafe_allow_html=True)
        st.markdown(f"### {outcome}")
        st.write(decision.get("rationale", "Review the evidence before making a decision."))
        st.caption(f"Two-sided p-value: {conv['p_value']:.4g} · α = {alpha:.2f}")
        st.markdown("---")
        st.markdown("**Executive decision brief**")
        status_text = "Significant" if conv["p_value"] < alpha else "Not significant"
        quality_text = "Review required" if validation.get("material_failure") else "No blocking issue detected"
        if validation.get("material_failure"):
            recommendation = "Pause interpretation. Investigate assignment, eligibility and instrumentation issues before using this result for a product decision."
        elif conv["p_value"] < alpha and conv["absolute_lift"] > 0:
            recommendation = "Positive conversion signal. Review prespecified guardrails and practical impact before considering a controlled rollout."
        elif conv["p_value"] < alpha and conv["absolute_lift"] < 0:
            recommendation = "Negative conversion signal. Do not roll out on conversion grounds; investigate the effect and check guardrails."
        else:
            recommendation = "Inconclusive. Do not declare a winner. Check the planned sample size and duration; continue only under a prespecified stopping plan."
        summary_rows = [
            {"Decision factor": "Observed treatment effect", "Result": f"{conv['absolute_lift'] * 100:+.2f} percentage points"},
            {"Decision factor": "95% confidence interval", "Result": f"[{conv['ci_low'] * 100:+.2f}, {conv['ci_high'] * 100:+.2f}] percentage points"},
            {"Decision factor": "Statistical evidence", "Result": f"{status_text} · p = {conv['p_value']:.4g} · α = {alpha:.2f}"},
            {"Decision factor": "Data quality", "Result": quality_text},
            {"Decision factor": "Recommended next action", "Result": recommendation},
        ]
        st.dataframe(pd.DataFrame(summary_rows), use_container_width=True, hide_index=True, column_config={"Decision factor": st.column_config.TextColumn(width="medium"), "Result": st.column_config.TextColumn(width="large")})
        st.info(recommendation)
    n1, n2, n3 = st.columns(3)
    n1.metric("Eligible users analysed", f"{len(eligible):,}")
    n2.metric("Control users", f"{int(conv['control_n']):,}")
    n3.metric("Treatment users", f"{int(conv['treatment_n']):,}")
    st.warning("Decision support, not an automatic release gate. Confirm randomization, exposure, attribution windows and guardrail metrics before shipping.")

# Data quality
with tabs[1]:
    st.markdown("## Data quality & experiment integrity")
    st.caption("Resolve material integrity issues before interpreting treatment effects.")
    checks = validation["checks"].copy()
    st.dataframe(checks, use_container_width=True, hide_index=True)
    q1, q2, q3 = st.columns(3)
    q1.metric("Raw rows", f"{validation['raw_rows']:,}")
    q2.metric("Unique users", f"{validation['unique_users']:,}")
    q3.metric("Duplicate-user rows", f"{max(validation['raw_rows'] - validation['unique_users'], 0):,}")
    if validation["material_failure"]:
        st.error("Material integrity issues detected. Treat statistical results as descriptive and block a launch decision.")
    else:
        st.success("No blocking issue detected by the current validator. Review all informational checks before interpretation.")

# Design & power
with tabs[2]:
    st.markdown("## Plan the experiment")
    st.caption("Estimate the sample required to detect a specified absolute change in conversion.")
    try:
        target_rate = min(baseline + mde, 0.99)
        plan = sample_size_two_proportions(baseline, target_rate, alpha, power)
        p1, p2, p3, p4 = st.columns(4)
        p1.metric("Required per arm", f"{plan['n_per_arm']:,}")
        p2.metric("Total sample", f"{plan['total_n']:,}")
        p3.metric("Absolute MDE", f"{mde:.1%}")
        p4.metric("Estimated duration", f"{plan['total_n'] / traffic:.1f} days")
        st.markdown('<div class="panel"><div class="panel-title">Planning assumptions</div><div class="panel-sub">Equal allocation · two-sided test · fixed sample design</div></div>', unsafe_allow_html=True)
        st.write(f"- Baseline conversion: **{baseline:.1%}**")
        st.write(f"- Target conversion: **{target_rate:.1%}**")
        st.write(f"- Significance level: **{alpha:.2f}**")
        st.write(f"- Target power: **{power:.0%}**")
        st.caption("Duration is a simple traffic-based estimate. It does not account for ramp-up, exclusions, seasonality or delayed outcomes.")
    except Exception as exc:
        st.error(f"Unable to calculate the sample-size plan: {exc}")

# Statistical results
with tabs[3]:
    st.markdown("## Statistical evidence")
    s1, s2, s3 = st.columns([0.8, 0.8, 1.6])
    s1.metric("P-value", f"{conv['p_value']:.5f}")
    s2.metric("Significance threshold", f"{alpha:.2f}")
    s3.metric("Treatment-effect 95% CI", f"{conv['ci_low']:+.2%} to {conv['ci_high']:+.2%}")
    significant = conv["p_value"] < alpha
    if significant:
        st.success("The observed conversion difference is statistically significant at the selected threshold.")
    else:
        st.info("**Inconclusive:** the observed difference is not statistically significant at the selected threshold. This does not establish equivalence or rule out a meaningful effect.")

    ci_low_pp = conv["ci_low"] * 100
    ci_high_pp = conv["ci_high"] * 100
    st.markdown("#### How to read this interval")
    st.write(
        f"The estimated treatment effect is **{conv['absolute_lift'] * 100:+.2f} percentage points**. "
        f"The 95% confidence interval runs from **{ci_low_pp:+.2f} to {ci_high_pp:+.2f} percentage points**. "
        "Because the interval includes zero, the data is compatible with a modest negative effect as well as a small positive effect. "
        "Use the interval to judge plausible effect sizes; do not treat the p-value alone as a launch decision."
    )

    if revenue_available:
        st.markdown("### Revenue per eligible user")
        try:
            continuous = analyze_continuous(eligible, "revenue_per_user")
            st.json(continuous)
        except Exception as exc:
            st.warning(f"Continuous-metric analysis could not be computed: {exc}")
        st.caption("Conversion uses a two-proportion test and a score-based interval approximation. Revenue per user can be skewed; interpret the Welch test cautiously.")
    else:
        st.markdown("### Revenue analysis")
        st.caption("ⓘ Revenue is unavailable for this dataset: it contains a binary conversion outcome but no order-value or revenue field. Varianta intentionally suppresses revenue estimates rather than inventing results.")

# Segments
with tabs[4]:
    st.markdown("## Segment exploration")
    st.caption("Use segments to generate hypotheses, not to cherry-pick a winner after the fact.")
    segment_options = ["device_type", "country", "acquisition_channel", "is_new_customer"] if revenue_available else ["visit_day"]
    segment_col = st.selectbox("Break down by", segment_options)
    seg = segment_conversion(eligible, segment_col, alpha=alpha)
    if not seg.empty:
        st.dataframe(seg, use_container_width=True, hide_index=True)
        fig = px.scatter(seg, x="control_rate", y="treatment_rate", size="n_total", color="segment",
                         hover_name="segment", labels={"control_rate":"Control conversion", "treatment_rate":"Treatment conversion", "n_total":"Users"},
                         title="Segment conversion: treatment vs control")
        fig.add_shape(type="line", x0=0, y0=0, x1=1, y1=1, line=dict(color="#a5abc0", dash="dash"))
        fig.update_layout(height=440, margin=dict(l=10,r=10,t=50,b=10), xaxis=dict(tickformat=".0%", gridcolor="#edf0f6"), yaxis=dict(tickformat=".0%", gridcolor="#edf0f6"), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No segment results are available for this dimension.")
    st.caption("Even adjusted p-values do not eliminate all risks from post-hoc exploration, small groups or unmeasured confounding.")

# Business impact
with tabs[5]:
    st.markdown("## Translate lift into business impact")
    st.caption("Scenario projection based on observed absolute lift and user-provided assumptions.")
    b1, b2, b3 = st.columns(3)
    b1.metric("Incremental conversions", f"{impact['incremental_conversions']:+,.0f}")
    if revenue_available:
        b2.metric("Projected incremental revenue", f"${impact['incremental_revenue']:+,.0f}")
        b3.metric("Projected contribution impact", f"${impact['contribution_impact']:+,.0f}")
        st.markdown('<div class="panel"><div class="panel-title">Projection assumptions</div><div class="panel-sub">Observed average order value is estimated from purchasing users in the selected dataset. Traffic and margin are configured in the sidebar.</div></div>', unsafe_allow_html=True)
    else:
        b2.metric("Revenue projection", "Unavailable")
        b3.metric("Contribution impact", "Unavailable")
        st.markdown('<div class="panel"><div class="panel-title">Conversion-only dataset</div><div class="panel-sub">This source does not contain order value or margin data. Revenue and contribution projections are intentionally suppressed rather than fabricated.</div></div>', unsafe_allow_html=True)
    assumptions = [
        {"Assumption": "Projection population", "Value": f"{business_traffic:,} users"},
        {"Assumption": "Observed absolute conversion lift", "Value": f"{conv['absolute_lift']:+.2%}"},
    ]
    if revenue_available:
        assumptions.extend([
            {"Assumption": "Observed average order value", "Value": f"${observed_aov:,.2f}"},
            {"Assumption": "Contribution margin per order", "Value": f"${margin:,.2f}"},
        ])
    st.dataframe(pd.DataFrame(assumptions), use_container_width=True, hide_index=True)
    st.json(impact if revenue_available else {k: v for k, v in impact.items() if k not in {"incremental_revenue", "contribution_impact", "assumed_average_order_value", "contribution_margin_per_order"}})
    st.warning("This is a scenario estimate, not realized revenue or a forecast interval. It assumes observed lift persists at the projected scale.")

# Decision & exports
with tabs[6]:
    st.markdown("## Recommendation & export")
    st.markdown(f"### {decision.get('outcome', 'Review required')}")
    st.write(decision.get("rationale", "No rationale was provided by the decision engine."))
    st.markdown("**Recommended next action**")
    st.info(decision.get("next_action", "Review experiment quality and statistical evidence."))
    report_json = json.dumps(report, indent=2, default=str)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.download_button("Download JSON report", report_json, file_name="varianta_report.json", mime="application/json", use_container_width=True)
    with c2:
        st.download_button("Download analysis CSV", eligible.to_csv(index=False), file_name="analysis_ready_data.csv", mime="text/csv", use_container_width=True)
    with c3:
        st.download_button("Download quality checks", validation["checks"].to_csv(index=False), file_name="data_quality_report.csv", mime="text/csv", use_container_width=True)

# Data explorer
with tabs[7]:
    st.markdown("## Data explorer")
    st.caption("Inspect the rows used for analysis and export the source dataset.")
    d1, d2, d3 = st.columns(3)
    d1.metric("Source rows", f"{len(df):,}")
    d2.metric("Analysis rows", f"{len(eligible):,}")
    d3.metric("Columns", f"{len(df.columns):,}")
    st.dataframe(eligible.head(250), use_container_width=True, hide_index=True)
    st.download_button("Download source dataset", df.to_csv(index=False), file_name="varianta_dataset.csv", mime="text/csv")

st.markdown(
    '<div class="footer-note">Varianta · Experiment analysis and decision support · '
    'Validate your instrumentation, metric definitions and statistical assumptions before making product decisions.</div>',
    unsafe_allow_html=True,
)
