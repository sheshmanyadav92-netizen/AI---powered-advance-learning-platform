from types import SimpleNamespace

from backend.services.career_matching import calculate_role_match, compare_roles


def test_weighted_match_percentage_and_gaps():
    role = SimpleNamespace(
        id=1,
        name="Example Developer",
        skills=[
            SimpleNamespace(skill="Python", required_level=80, weight=2),
            SimpleNamespace(skill="React", required_level=70, weight=1),
            SimpleNamespace(skill="SQL", required_level=60, weight=1),
        ],
    )
    skills = [
        SimpleNamespace(skill="Python", level=40),
        SimpleNamespace(skill="SQL", level=60),
    ]

    result = calculate_role_match(skills, role)

    assert result["match_percent"] == 50.0
    assert result["missing"] == ["React"]
    assert result["weak"] == ["Python"]
    assert result["satisfied"] == ["SQL"]


def test_compare_roles_sorts_by_match_percentage():
    skills = [SimpleNamespace(skill="Python", level=80)]
    roles = [
        SimpleNamespace(
            id=1,
            name="Low match",
            skills=[SimpleNamespace(skill="React", required_level=70, weight=1)],
        ),
        SimpleNamespace(
            id=2,
            name="High match",
            skills=[SimpleNamespace(skill="Python", required_level=80, weight=1)],
        ),
    ]

    matches = compare_roles(skills, roles)

    assert [match["role"] for match in matches] == ["High match", "Low match"]
