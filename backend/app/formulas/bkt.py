"""Bayesian Knowledge Tracing (BKT) Model implementation.
Reference: Corbett, A. T., & Anderson, J. R. (1994).
Knowledge tracing: Modeling the acquisition of procedural knowledge.
User Modeling and User-Adapted Interaction, 4(4), 253-278.

Parameters:
- P(L0): Initial mastery belief (0.30)
- P(T): Probability of learning / state transition (0.15)
- P(G): Probability of guessing when skill is unmastered (0.20)
- P(S): Probability of slipping when skill is mastered (0.10)
"""

DEFAULT_P_L0 = 0.30
DEFAULT_P_T = 0.15
DEFAULT_P_G = 0.20
DEFAULT_P_S = 0.10

def bkt_update(
    p_prev: float,
    is_correct: bool,
    p_T: float = DEFAULT_P_T,
    p_G: float = DEFAULT_P_G,
    p_S: float = DEFAULT_P_S
) -> float:
    """Updates the mastery belief P(Ln) given evidence (correct or incorrect).
    Step 1: Evidence update (posterior probability given observation)
    Step 2: Transition update (probability of learning prior to next opportunity)
    """
    p_prev = max(0.0001, min(0.9999, float(p_prev)))

    if is_correct:
        numerator = p_prev * (1.0 - p_S)
        denominator = numerator + (1.0 - p_prev) * p_G
        p_evidence = numerator / denominator
    else:
        numerator = p_prev * p_S
        denominator = numerator + (1.0 - p_prev) * (1.0 - p_G)
        p_evidence = numerator / denominator

    # Learning transition update
    p_next = p_evidence + (1.0 - p_evidence) * p_T
    return max(0.0, min(1.0, p_next))


def is_remediation_needed(
    p_mastery: float,
    attempts_count: int,
    threshold: float = 0.50,
    min_attempts: int = 3
) -> bool:
    """Trigger for adaptation:
    If P(Ln) < 0.5 after 3+ attempts on a skill -> flagged as needing remediation / easier resources.
    """
    return (attempts_count >= min_attempts) and (p_mastery < threshold)
