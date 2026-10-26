"""Statistical metrics for user-randomized A/B tests."""
import numpy as np
import pandas as pd
from scipy.stats import norm, ttest_ind
from statsmodels.stats.proportion import proportions_ztest
from statsmodels.stats.multitest import multipletests

def analyze_conversion(df, alpha=0.05):
    c=df[df.variant=="Control"]; t=df[df.variant=="Treatment"]
    n1,n2=len(c),len(t)
    x1=int(c.purchase_completed.astype(bool).sum()); x2=int(t.purchase_completed.astype(bool).sum())
    p1=x1/n1 if n1 else 0; p2=x2/n2 if n2 else 0
    diff=p2-p1
    if n1 and n2:
        # Degenerate outcomes (both arms all-zero or all-one) have zero pooled
        # variance in the z-test. Return a neutral p-value rather than NaN.
        if (x1 == 0 and x2 == 0) or (x1 == n1 and x2 == n2):
            pval = 1.0
        else:
            _,pval=proportions_ztest([x2,x1],[n2,n1],alternative="two-sided")
            if not np.isfinite(pval):
                pval = 1.0 if p1 == p2 else 0.0
        # Newcombe-Wilson score interval for difference.
        def wilson(x,n,z):
            ph=x/n; den=1+z*z/n
            center=(ph+z*z/(2*n))/den
            half=z*np.sqrt(ph*(1-ph)/n+z*z/(4*n*n))/den
            return center-half,center+half
        z=norm.ppf(1-alpha/2)
        l1,u1=wilson(x1,n1,z); l2,u2=wilson(x2,n2,z)
        lo=diff-np.sqrt((p2-l2)**2+(u1-p1)**2)
        hi=diff+np.sqrt((u2-p2)**2+(p1-l1)**2)
    else:
        pval=1.0; lo=float("nan"); hi=float("nan")
    return {"control_n":n1,"treatment_n":n2,"control_conversions":x1,"treatment_conversions":x2,
    "control_rate":p1,"treatment_rate":p2,"absolute_lift":diff,"relative_lift":diff/p1 if p1 else float("nan"),
    "ci_low":lo,"ci_high":hi,"p_value":float(pval),"alpha":alpha,
    "significant":bool(pval<alpha),"method":"Two-sided two-proportion z-test; Newcombe-style Wilson score CI"}

def analyze_continuous(df, metric):
    work=df.copy()
    if metric=="revenue_per_user":
        work[metric]=np.where(work.purchase_completed.astype(bool),pd.to_numeric(work.order_value,errors="coerce").fillna(0),0)
    c=pd.to_numeric(work.loc[work.variant=="Control",metric],errors="coerce").dropna()
    t=pd.to_numeric(work.loc[work.variant=="Treatment",metric],errors="coerce").dropna()
    if len(c)<2 or len(t)<2:
        return {"metric":metric,"control_mean":float(c.mean()) if len(c) else None,"treatment_mean":float(t.mean()) if len(t) else None,"difference":None,"p_value":None}
    result=ttest_ind(t,c,equal_var=False,nan_policy="omit")
    return {"metric":metric,"control_mean":float(c.mean()),"treatment_mean":float(t.mean()),"difference":float(t.mean()-c.mean()),"p_value":float(result.pvalue),"method":"Welch independent-samples t-test"}
