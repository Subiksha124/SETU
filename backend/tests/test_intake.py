import pytest
from app.agents.intake_agent import process_intake_message, parse_income, parse_class
from app.database import init_db

@pytest.fixture(autouse=True)
def setup_database():
    init_db()

def test_parse_income():
    assert parse_income("Our annual income is 1.5 lakhs") == 150000
    assert parse_income("200000 per annum") == 200000
    assert parse_income("around 80k") == 80000
    assert parse_income("below 1 lakh") == 90000

def test_parse_class():
    assert parse_class("Completed 12th standard") == 12
    assert parse_class("I finished 10th sslc") == 10
    assert parse_class("Passed 11th grade") == 11

def test_intake_flow_step_by_step():
    session_id = "test-session-123"
    
    # Step 1: select class (e.g. 12th)
    r1 = process_intake_message(session_id=session_id, menu_choice=3)
    assert r1["profile"]["completed_class"] == 12
    assert "gender" in r1["missing_fields"]

    # Step 2: select gender (e.g. female = 1)
    r2 = process_intake_message(session_id=session_id, menu_choice=1)
    assert r2["profile"]["gender"] == "female"
    assert "income" in r2["missing_fields"]

    # Step 3: select income (e.g. option 2: 1-2 lakhs)
    r3 = process_intake_message(session_id=session_id, menu_choice=2)
    assert r3["profile"]["income"] == 180000
    assert "category" in r3["missing_fields"]

    # Step 4: select category (e.g. option 1: BC)
    r4 = process_intake_message(session_id=session_id, menu_choice=1)
    assert r4["profile"]["category"] == "BC"
    assert r4["is_complete"] is True
    assert r4["ready_for_confirmation"] is True

def test_intake_confirmation_returns_matched_schemes_with_specific_urls():
    session_id = "test-session-confirm"
    process_intake_message(session_id=session_id, menu_choice=3)  # 12th
    process_intake_message(session_id=session_id, menu_choice=1)  # female
    process_intake_message(session_id=session_id, menu_choice=2)  # 1.8L
    process_intake_message(session_id=session_id, menu_choice=1)  # BC
    
    # Step 5: Confirm profile
    r_confirm = process_intake_message(session_id=session_id, menu_choice=1)
    assert r_confirm["matched_schemes"] is not None
    assert len(r_confirm["matched_schemes"]) > 0
    
    # Verify each scheme has a valid specific official_url
    for s in r_confirm["matched_schemes"]:
        assert s["official_url"].startswith("https://")
        # Ensure not generic unrouted NSP homepage
        assert s["official_url"] != "https://scholarships.gov.in"
