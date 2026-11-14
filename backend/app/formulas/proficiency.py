"""Skill proficiency formula implementation with full float precision.
Formula:
P_s = w1 * A_s + w2 * Q_s + w3 * E_s
where:
- A_s: self-assessed level (0-100)
- Q_s: average quiz/assessment score (0-100)
- E_s: evidence score from listed projects/certs (0-100)
- w1 + w2 + w3 = 1. Default: w1=0.2, w2=0.5, w3=0.3
Note: Full float precision is preserved (no premature rounding).
"""

def calculate_skill_proficiency(
    A_s: float,
    Q_s: float,
    E_s: float,
    w1: float = 0.2,
    w2: float = 0.5,
    w3: float = 0.3
) -> float:
    a = max(0.0, min(100.0, float(A_s)))
    q = max(0.0, min(100.0, float(Q_s)))
    e = max(0.0, min(100.0, float(E_s)))

    total_w = w1 + w2 + w3
    if abs(total_w - 1.0) > 1e-6:
        w1, w2, w3 = w1 / total_w, w2 / total_w, w3 / total_w

    score = (w1 * a) + (w2 * q) + (w3 * e)
    return max(0.0, min(100.0, score))
