from types import SimpleNamespace

from backend.services.skill_analysis import analyze_skills


def test_skill_analysis_classifies_strength_developing_and_weakness():
    result = analyze_skills(
        [
            SimpleNamespace(skill="Python", level=70),
            SimpleNamespace(skill="SQL", level=60),
            SimpleNamespace(skill="HTML", level=40),
        ]
    )

    assert result["strengths"] == ["Python"]
    assert result["weaknesses"] == ["HTML"]
    assert result["skills"] == [
        {"skill": "HTML", "level": 40, "status": "weakness"},
        {"skill": "Python", "level": 70, "status": "strength"},
        {"skill": "SQL", "level": 60, "status": "developing"},
    ]
