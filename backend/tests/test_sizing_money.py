from solarsabha.tools import sizing

def test_recommended_size_matches_worked_example():
    plan = sizing.size_system(annual_kwh=60000, flats=50)
    assert plan["recommended_kw"] == 36
    assert plan["subsidy_ceiling_kw"] == 150

def test_ceiling_is_respected():
    plan = sizing.size_system(annual_kwh=900000, flats=10)  # huge load, tiny society
    assert plan["recommended_kw"] <= 30

def test_money_summary_worked_example():
    m = sizing.money_summary(36)
    assert m["total_cost"] == 1_800_000 and m["subsidy"] == 648_000 and m["net_cost"] == 1_152_000
    assert m["generation_kwh_year"] == 50_400
    assert m["payback_years"] == 3.3
    assert round(m["co2_tonnes_year"]) == 36

def test_bad_input():
    import pytest
    with pytest.raises(ValueError):
        sizing.size_system(0, 10)
