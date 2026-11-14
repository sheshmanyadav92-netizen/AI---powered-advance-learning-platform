"""Pytest unit tests for all mathematical and probabilistic formulas.
Every test function contains hand-computed expected values in comments
above each assertion to guarantee mathematical rigor.
Full float precision is tested with pytest.approx or display-time rounding.
"""
import pytest
from app.formulas.proficiency import calculate_skill_proficiency
from app.formulas.gap import calculate_skill_gap
from app.formulas.readiness import calculate_career_readiness, calculate_cosine_fit
from app.formulas.recommendation import calculate_recommendation_priority, calculate_tag_similarity
from app.formulas.bkt import bkt_update, is_remediation_needed
from app.formulas.elo import calculate_elo_update


class TestSkillProficiencyFormula:
    def test_proficiency_general_case(self):
        # HAND-COMPUTED EXPECTED VALUE:
        # A_s = 60, Q_s = 80, E_s = 50
        # w1 = 0.2, w2 = 0.5, w3 = 0.3
        # P_s = (0.2 * 60) + (0.5 * 80) + (0.3 * 50)
        # P_s = 12.0 + 40.0 + 15.0 = 67.0
        expected = 67.0
        result = calculate_skill_proficiency(A_s=60, Q_s=80, E_s=50)
        assert result == pytest.approx(expected, abs=1e-4)

    def test_proficiency_sample_python_scenario(self):
        # HAND-COMPUTED EXPECTED VALUE:
        # Python: Self-report A_s = 80, Quiz Q_s = 70, Evidence E_s = 60
        # P_s = (0.2 * 80) + (0.5 * 70) + (0.3 * 60) = 16.0 + 35.0 + 18.0 = 69.0
        expected = 69.0
        result = calculate_skill_proficiency(A_s=80, Q_s=70, E_s=60)
        assert result == pytest.approx(expected, abs=1e-4)

    def test_proficiency_boundary_zero_and_hundred(self):
        # HAND-COMPUTED EXPECTED VALUE:
        # All zeros -> 0.0
        assert calculate_skill_proficiency(0, 0, 0) == 0.0
        # All hundreds -> 100.0
        assert calculate_skill_proficiency(100, 100, 100) == 100.0


class TestSkillGapFormula:
    def test_skill_gap_with_deficit(self):
        # HAND-COMPUTED EXPECTED VALUE:
        # Target R_s = 80.0, Current P_s = 69.0
        # G_s = max(0, 80.0 - 69.0) = 11.0
        expected = 11.0
        result = calculate_skill_gap(R_s=80.0, P_s=69.0)
        assert result == pytest.approx(expected, abs=1e-4)

    def test_skill_gap_when_proficiency_exceeds_requirement(self):
        # HAND-COMPUTED EXPECTED VALUE:
        # Target R_s = 60.0, Current P_s = 75.0
        # G_s = max(0, 60.0 - 75.0) = 0.0
        expected = 0.0
        result = calculate_skill_gap(R_s=60.0, P_s=75.0)
        assert result == expected

    def test_skill_gap_completely_missing_skill(self):
        # HAND-COMPUTED EXPECTED VALUE:
        # Target JavaScript R_s = 80.0, Current P_s = 0.0
        # G_s = max(0, 80.0 - 0.0) = 80.0
        expected = 80.0
        result = calculate_skill_gap(R_s=80.0, P_s=0.0)
        assert result == expected


class TestCareerReadinessFormula:
    def test_readiness_sample_fullstack_case(self):
        # HAND-COMPUTED EXPECTED VALUE:
        # Sample role: Full Stack Developer
        # Skills (P_s, R_s, I_s):
        # Python:     P=70, R=70, I=0.8 -> P*I = 56.0,  R*I = 56.0
        # SQL:        P=60, R=60, I=0.6 -> P*I = 36.0,  R*I = 36.0
        # HTML:       P=50, R=50, I=0.5 -> P*I = 25.0,  R*I = 25.0
        # JavaScript: P=0,  R=80, I=1.0 -> P*I = 0.0,   R*I = 80.0
        # React:      P=0,  R=75, I=1.0 -> P*I = 0.0,   R*I = 75.0
        # Node.js:    P=0,  R=70, I=0.9 -> P*I = 0.0,   R*I = 63.0
        #
        # Numerator   = 56 + 36 + 25 + 0 + 0 + 0 = 117.0
        # Denominator = 56 + 36 + 25 + 80 + 75 + 63 = 335.0
        # Ratio       = 117.0 / 335.0 = 0.3492537...
        # Display Readiness % = 34.93%
        expected = 34.92537
        skills_data = [
            (70.0, 70.0, 0.8),
            (60.0, 60.0, 0.6),
            (50.0, 50.0, 0.5),
            (0.0, 80.0, 1.0),
            (0.0, 75.0, 1.0),
            (0.0, 70.0, 0.9),
        ]
        result = calculate_career_readiness(skills_data)
        assert result == pytest.approx(expected, abs=1e-3)
        assert round(result, 2) == 34.93

    def test_cosine_fit_sample_fullstack_case(self):
        # HAND-COMPUTED EXPECTED VALUE:
        # P = [70, 60, 50, 0, 0, 0]
        # R = [70, 60, 50, 80, 75, 70]
        # Dot product P . R = 4900 + 3600 + 2500 + 0 + 0 + 0 = 11000.0
        # ||P|| = sqrt(4900 + 3600 + 2500) = sqrt(11000) = 104.8808848
        # ||R|| = sqrt(4900 + 3600 + 2500 + 6400 + 5625 + 4900) = sqrt(27925) = 167.1077496
        # CosineFit = 11000.0 / (104.8808848 * 167.1077496) = 0.627624...
        expected = 0.6276
        p_vec = [70.0, 60.0, 50.0, 0.0, 0.0, 0.0]
        r_vec = [70.0, 60.0, 50.0, 80.0, 75.0, 70.0]
        result = calculate_cosine_fit(p_vec, r_vec)
        assert result == pytest.approx(expected, abs=1e-3)


class TestRecommendationPriorityFormula:
    def test_priority_missing_skills_ranking(self):
        # HAND-COMPUTED EXPECTED VALUES:
        # JavaScript: G_s = 80, I_s = 1.0, T_s = 20 hrs
        # Priority = (80 * 1.0) / 20 = 4.0
        js_priority = calculate_recommendation_priority(G_s=80.0, I_s=1.0, T_s=20.0)
        assert js_priority == 4.0

        # React: G_s = 75, I_s = 1.0, T_s = 25 hrs
        # Priority = (75 * 1.0) / 25 = 3.0
        react_priority = calculate_recommendation_priority(G_s=75.0, I_s=1.0, T_s=25.0)
        assert react_priority == 3.0

        # Node.js: G_s = 70, I_s = 0.9, T_s = 30 hrs
        # Priority = (70 * 0.9) / 30 = 63.0 / 30 = 2.1
        node_priority = calculate_recommendation_priority(G_s=70.0, I_s=0.9, T_s=30.0)
        assert node_priority == 2.1

        # JavaScript (4.0) > React (3.0) > Node.js (2.1)
        assert js_priority > react_priority > node_priority

    def test_tag_similarity_calculation(self):
        # HAND-COMPUTED EXPECTED VALUE:
        # Gap tags: ["javascript", "frontend", "dom"]
        # Res tags: ["javascript", "es6", "dom"]
        # Vocabulary: [javascript, frontend, dom, es6]
        # Gap vector: [1, 1, 1, 0] -> ||Gap|| = sqrt(1+1+1) = sqrt(3)
        # Res vector: [1, 0, 1, 1] -> ||Res|| = sqrt(1+1+1) = sqrt(3)
        # Dot product = 1*1 + 1*0 + 1*1 + 0*1 = 2
        # Sim = 2 / (sqrt(3) * sqrt(3)) = 2 / 3 = 0.66666...
        expected = 2.0 / 3.0
        sim = calculate_tag_similarity(
            gap_tags=["javascript", "frontend", "dom"],
            resource_tags=["javascript", "es6", "dom"]
        )
        assert sim == pytest.approx(expected, abs=1e-4)


class TestBayesianKnowledgeTracingFormula:
    def test_bkt_correct_step(self):
        # HAND-COMPUTED EXPECTED VALUE:
        # Initial P(L0) = 0.30, P(T) = 0.15, P(G) = 0.20, P(S) = 0.10
        # Evidence = correct:
        # Numerator = 0.30 * (1 - 0.10) = 0.30 * 0.90 = 0.27
        # Denominator = 0.27 + (1 - 0.30) * 0.20 = 0.27 + (0.70 * 0.20) = 0.27 + 0.14 = 0.41
        # P(L1 | correct) = 0.27 / 0.41 = 0.658536585
        # Learning transition:
        # P(L1) = P(L1 | correct) + (1 - P(L1 | correct)) * P(T)
        # P(L1) = 0.658536585 + (1 - 0.658536585) * 0.15 = 0.709756...
        expected = 0.709756
        result = bkt_update(p_prev=0.30, is_correct=True, p_T=0.15, p_G=0.20, p_S=0.10)
        assert result == pytest.approx(expected, abs=1e-4)

    def test_bkt_incorrect_step(self):
        # HAND-COMPUTED EXPECTED VALUE:
        # Initial P(L0) = 0.30, P(T) = 0.15, P(G) = 0.20, P(S) = 0.10
        # Evidence = incorrect:
        # Numerator = 0.30 * 0.10 = 0.03
        # Denominator = 0.03 + (1 - 0.30) * (1 - 0.20) = 0.03 + 0.70 * 0.80 = 0.03 + 0.56 = 0.59
        # P(L1 | incorrect) = 0.03 / 0.59 = 0.050847457
        # Learning transition:
        # P(L1) = 0.050847457 + (1 - 0.050847457) * 0.15 = 0.193220...
        expected = 0.193220
        result = bkt_update(p_prev=0.30, is_correct=False, p_T=0.15, p_G=0.20, p_S=0.10)
        assert result == pytest.approx(expected, abs=1e-4)

    def test_bkt_remediation_trigger(self):
        # Trigger condition: P(Ln) < 0.5 after 3+ attempts
        # Case 1: p_mastery=0.45, attempts=3 -> True (Flagged for remediation)
        assert is_remediation_needed(p_mastery=0.45, attempts_count=3) is True

        # Case 2: p_mastery=0.60, attempts=3 -> False (Above threshold)
        assert is_remediation_needed(p_mastery=0.60, attempts_count=3) is False

        # Case 3: p_mastery=0.40, attempts=2 -> False (Under 3 attempts)
        assert is_remediation_needed(p_mastery=0.40, attempts_count=2) is False


class TestEloItemDifficultyFormula:
    def test_elo_update(self):
        # HAND-COMPUTED EXPECTED VALUE:
        # Rating = 1200, Difficulty = 1200, Actual = 1.0 (Correct), K = 32
        # Expected = 1 / (1 + 10^((1200 - 1200) / 400)) = 1 / (1 + 10^0) = 1 / 2 = 0.5
        # NewRating = 1200 + 32 * (1.0 - 0.5) = 1200 + 16 = 1216.0
        expected = 1216.0
        result = calculate_elo_update(
            learner_rating=1200.0,
            item_difficulty=1200.0,
            actual_outcome=1.0,
            k=32.0
        )
        assert result == expected
