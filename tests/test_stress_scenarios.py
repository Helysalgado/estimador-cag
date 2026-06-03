from evals.stress.scenarios import all_scenarios, get_scenario


def test_each_scenario_has_at_least_20_turns():
    for scenario in all_scenarios():
        assert len(scenario.turns) >= 20


def test_get_scenario_unknown_raises():
    try:
        get_scenario("nonexistent")
    except ValueError as exc:
        assert "nonexistent" in str(exc)
    else:
        raise AssertionError("expected ValueError")
