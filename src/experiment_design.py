"""Sample-size calculations for two independent proportions."""
from statsmodels.stats.power import NormalIndPower
from statsmodels.stats.proportion import proportion_effectsize

def sample_size_two_proportions(p_control, p_treatment, alpha=0.05, power=0.8, ratio=1.0):
    if not (0 < p_control < 1 and 0 < p_treatment < 1):
        raise ValueError("Both conversion rates must be strictly between 0 and 1.")
    if not (0 < alpha < 1 and 0 < power < 1 and ratio > 0):
        raise ValueError("alpha and power must be between 0 and 1; ratio must be positive.")
    effect=abs(proportion_effectsize(p_control,p_treatment))
    if effect == 0:
        raise ValueError("Target conversion must differ from baseline.")
    analysis=NormalIndPower()
    n_control=analysis.solve_power(effect_size=effect, power=power, alpha=alpha, ratio=ratio, alternative="two-sided")
    n_treatment=n_control*ratio
    n1=int(__import__("math").ceil(n_control)); n2=int(__import__("math").ceil(n_treatment))
    return {"n_per_arm":max(n1,n2),"n_control":n1,"n_treatment":n2,"total_n":n1+n2,"effect_size_h":effect,"alpha":alpha,"target_power":power}
