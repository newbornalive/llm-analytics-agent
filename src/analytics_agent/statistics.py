import math
from collections import defaultdict
from itertools import combinations
from scipy.stats import chi2_contingency, fisher_exact


def wilson(successes, n):
    if not isinstance(n, int) or not isinstance(successes, int) or n <= 0 or not 0 <= successes <= n:
        raise ValueError("Wilson interval requires integer counts with 0 <= successes <= n and n > 0.")
    z = 1.959963984540054
    p = successes / n
    denom = 1 + z*z/n
    center = (p + z*z/(2*n)) / denom
    half = z*math.sqrt(p*(1-p)/n + z*z/(4*n*n)) / denom
    return [max(0.0, center-half), min(1.0, center+half)]


def holm(pvalues):
    if any(not math.isfinite(p) or not 0 <= p <= 1 for p in pvalues):
        raise ValueError("P-values must be finite probabilities.")
    adjusted = [0.0] * len(pvalues)
    floor = 0.0
    for rank, index in enumerate(sorted(range(len(pvalues)), key=pvalues.__getitem__)):
        floor = max(floor, min(1.0, (len(pvalues)-rank)*pvalues[index]))
        adjusted[index] = floor
    return adjusted


def analyze_rows(rows):
    if not rows:
        raise ValueError("No events matched the query; no statistical result was generated.")
    ids = set()
    groups = defaultdict(list)
    for row in rows:
        event_id, channel, converted = row["event_id"], row["channel"], row["converted"]
        if not isinstance(event_id, int) or event_id in ids:
            raise ValueError("Missing/invalid/duplicate event IDs; independence cannot be assessed.")
        if not isinstance(channel, str) or not channel.strip() or len(channel) > 200:
            raise ValueError("Channel labels must be nonempty strings of at most 200 characters.")
        if converted not in (0, 1) or not isinstance(converted, int):
            raise ValueError("converted must contain only nonmissing binary integers (0 or 1).")
        ids.add(event_id)
        groups[channel].append(converted)
    if len(groups) > 20:
        raise ValueError("At most 20 channels are supported for pairwise analysis.")
    summaries = [{"channel": k, "events": len(v), "conversions": sum(v), "rate": sum(v)/len(v),
                  "wilson_95_ci": wilson(sum(v), len(v))} for k, v in sorted(groups.items())]
    warnings = ["Observational comparison: channel differences do not establish causal effects.",
                "Unique event IDs do not prove independent subjects; repeated-user dependence cannot be checked without a user identifier.",
                "Wilson intervals assume independent Bernoulli events and are individual, not simultaneous, 95% intervals."]
    table = [[s["conversions"], s["events"]-s["conversions"]] for s in summaries]
    omnibus = {"method": "not_tested", "p_value": None, "reason": "At least two channels with outcome variation are needed."}
    if len(table) >= 2 and 0 < sum(t[0] for t in table) < len(rows):
        statistic, p, dof, expected = chi2_contingency(table, correction=False)
        if float(expected.min()) >= 5:
            omnibus = {"method": "Pearson chi-square", "statistic": float(statistic), "df": int(dof), "p_value": float(p), "min_expected_count": float(expected.min())}
        elif len(table) == 2:
            omnibus = {"method": "Fisher exact (two-sided)", "p_value": float(fisher_exact(table).pvalue), "reason": "Expected count below 5."}
        else:
            omnibus = {"method": "not_tested", "p_value": None, "reason": "Sparse expected counts: Pearson approximation withheld for more than two channels."}
    pairwise = []
    for a, b in combinations(summaries, 2):
        contingency = [[a["conversions"], a["events"]-a["conversions"]], [b["conversions"], b["events"]-b["conversions"]]]
        p = float(fisher_exact(contingency).pvalue)
        pairwise.append({"channels": [a["channel"], b["channel"]], "rate_difference": a["rate"]-b["rate"], "method": "Fisher exact (two-sided)", "p_value": p})
    for item, adjusted in zip(pairwise, holm([p["p_value"] for p in pairwise])):
        item["holm_adjusted_p"] = adjusted
    return {"sample_size": len(rows), "groups": summaries, "omnibus": omnibus, "pairwise": pairwise,
            "multiple_testing_family": "All reported pairwise channel comparisons; omnibus test is reported separately.", "warnings": warnings}
