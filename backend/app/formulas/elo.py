"""Elo-style adaptive difficulty calculation.
Kept separate from BKT mastery updates.
Formulas:
Expected = 1 / (1 + 10^((Difficulty - LearnerRating) / 400))
LearnerRating_new = LearnerRating_old + K * (ActualOutcome - Expected)
Where K = 32, ActualOutcome = 1.0 (correct) or 0.0 (incorrect).
"""
import math

K_FACTOR = 32.0

def calculate_expected_outcome(difficulty: float, learner_rating: float) -> float:
    """Calculates expected outcome probability for a learner against a difficulty rating."""
    exponent = (float(difficulty) - float(learner_rating)) / 400.0
    return 1.0 / (1.0 + math.pow(10.0, exponent))

def update_elo_rating(learner_rating: float, difficulty: float, actual_outcome: float) -> float:
    """Updates learner rating according to Elo formula.
    actual_outcome: 1.0 for correct, 0.0 for incorrect.
    """
    expected = calculate_expected_outcome(difficulty, learner_rating)
    outcome = 1.0 if actual_outcome >= 0.5 else 0.0
    new_rating = float(learner_rating) + K_FACTOR * (outcome - expected)
    return round(new_rating, 2)
