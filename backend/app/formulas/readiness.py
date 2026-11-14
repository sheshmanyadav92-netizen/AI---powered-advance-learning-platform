"""Career readiness score and vector similarity metric with full float precision.
Formulas:
1. Overall Career Readiness:
   Readiness = min(100, [ sum(P_s * I_s) / sum(R_s * I_s) ] * 100)
2. Cosine Similarity (CareerFit):
   CareerFit = (P . R) / (||P|| * ||R||)
"""
import math
from typing import List, Tuple

def calculate_career_readiness(
    skills_data: List[Tuple[float, float, float]]
) -> float:
    """Computes overall readiness score as an importance-weighted percentage.
    skills_data: list of tuples (P_s, R_s, I_s)
    """
    if not skills_data:
        return 0.0

    numerator = sum(max(0.0, float(p)) * max(0.0, float(i)) for p, r, i in skills_data)
    denominator = sum(max(0.0, float(r)) * max(0.0, float(i)) for p, r, i in skills_data)

    if denominator <= 0:
        return 100.0 if numerator > 0 else 0.0

    readiness = (numerator / denominator) * 100.0
    return min(100.0, max(0.0, readiness))


def calculate_cosine_fit(
    P_vector: List[float],
    R_vector: List[float]
) -> float:
    """Computes cosine similarity between current proficiency vector and required vector.
    CareerFit = (P . R) / (||P|| * ||R||)
    """
    if not P_vector or not R_vector or len(P_vector) != len(R_vector):
        return 0.0

    dot_product = sum(float(p) * float(r) for p, r in zip(P_vector, R_vector))
    norm_p = math.sqrt(sum(float(p) * float(p) for p in P_vector))
    norm_r = math.sqrt(sum(float(r) * float(r) for r in R_vector))

    if norm_p == 0.0 or norm_r == 0.0:
        return 0.0

    cosine = dot_product / (norm_p * norm_r)
    return max(0.0, min(1.0, cosine))
