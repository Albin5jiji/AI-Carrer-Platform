from app.services.readiness import READINESS_WEIGHTS, compute_overall


def test_required_components_exist_and_weights_are_exact():
    expected = {
        "academics": 15,
        "skills": 30,
        "projects": 20,
        "certifications": 10,
        "resume": 10,
        "interview": 15,
    }

    assert set(READINESS_WEIGHTS.keys()) == set(expected.keys())
    assert READINESS_WEIGHTS == expected
    assert sum(READINESS_WEIGHTS.values()) == 100


def test_weighted_score_uses_exact_backend_weights():
    components = {
        "academics": (100, ""),
        "skills": (100, ""),
        "projects": (100, ""),
        "certifications": (100, ""),
        "resume": (100, ""),
        "interview": (100, ""),
    }

    assert compute_overall(components) == 100

    components = {
        "academics": (50, ""),
        "skills": (100, ""),
        "projects": (100, ""),
        "certifications": (100, ""),
        "resume": (100, ""),
        "interview": (100, ""),
    }

    # 50*15% + 100*30% + 100*20% + 100*10% + 100*10% + 100*15% = 92.5 => 92
    assert compute_overall(components) == 92

    components = {
        "academics": (0, ""),
        "skills": (0, ""),
        "projects": (0, ""),
        "certifications": (0, ""),
        "resume": (0, ""),
        "interview": (0, ""),
    }

    assert compute_overall(components) == 0
