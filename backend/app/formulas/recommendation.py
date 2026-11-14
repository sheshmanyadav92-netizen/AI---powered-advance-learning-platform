"""Recommendation ranking and content matching formulas with full float precision.
Formulas:
1. Recommendation Priority Score:
   Priority_s = (G_s * I_s) / T_s
2. Content-matching score (TF-IDF / Tag-based Cosine Similarity):
   Sim(gap, resource) = (gap_vec . resource_vec) / (||gap_vec|| * ||resource_vec||)
"""
import math
from typing import List

def calculate_recommendation_priority(
    G_s: float,
    I_s: float,
    T_s: float
) -> float:
    """Computes ROI-based recommendation priority."""
    if T_s <= 0:
        T_s = 1.0  # Avoid division by zero, min 1 hour
    priority = (float(G_s) * float(I_s)) / float(T_s)
    return max(0.0, priority)


def calculate_tag_similarity(
    gap_tags: List[str],
    resource_tags: List[str]
) -> float:
    """Computes binary/frequency cosine similarity between gap tags and resource tags."""
    cleaned_gap = [t.strip().lower() for t in gap_tags if t.strip()]
    cleaned_res = [t.strip().lower() for t in resource_tags if t.strip()]

    if not cleaned_gap or not cleaned_res:
        return 0.0

    vocabulary = list(set(cleaned_gap + cleaned_res))
    gap_vec = [cleaned_gap.count(word) for word in vocabulary]
    res_vec = [cleaned_res.count(word) for word in vocabulary]

    dot_product = sum(g * r for g, r in zip(gap_vec, res_vec))
    norm_gap = math.sqrt(sum(g * g for g in gap_vec))
    norm_res = math.sqrt(sum(r * r for r in res_vec))

    if norm_gap == 0.0 or norm_res == 0.0:
        return 0.0

    return dot_product / (norm_gap * norm_res)
