import re
from typing import Dict, Any, Tuple, List, Optional
from .eligibility_agent import evaluate_eligibility

# Active in-memory sessions: session_id -> { profile, history, step }
_SESSIONS: Dict[str, Dict[str, Any]] = {}

def get_or_create_session(session_id: str) -> Dict[str, Any]:
    if session_id not in _SESSIONS:
        _SESSIONS[session_id] = {
            "profile": {
                "name": "Student",
                "state": "Tamil Nadu",
                "completed_class": None,
                "income": None,
                "category": None,
                "gender": None,
                "course_pursuing": None,
                "confirmed": False
            },
            "step": "class"
        }
    return _SESSIONS[session_id]

def parse_income(text: str) -> Optional[int]:
    """Parse income in various Indian formats: e.g. 1.5 lakhs, 200000, 80k, etc."""
    text_lower = text.lower().replace(",", "").strip()
    
    # Check for "below" phrases first
    if "below 1 lakh" in text_lower or "below one lakh" in text_lower:
        return 90000
    if "below 2 lakh" in text_lower or "below two lakh" in text_lower:
        return 180000
    if "below 2.5 lakh" in text_lower or "below 2.5" in text_lower:
        return 220000
    if "below 5 lakh" in text_lower:
        return 350000

    # Check for "lakh" or "lac"
    lakh_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:lakhs?|lacs?|l)\b', text_lower)
    if lakh_match:
        val = float(lakh_match.group(1))
        return int(val * 100000)
    
    # Check for "k" (e.g. 80k)
    k_match = re.search(r'(\d+(?:\.\d+)?)\s*k\b', text_lower)
    if k_match:
        val = float(k_match.group(1))
        return int(val * 1000)
    
    # Check for standalone numbers
    num_match = re.search(r'\b(\d{4,8})\b', text_lower)
    if num_match:
        return int(num_match.group(1))
    
    return None

def parse_class(text: str) -> Optional[int]:
    text_lower = text.lower()
    if "12" in text_lower or "twelfth" in text_lower or "+2" in text_lower or "hsc" in text_lower:
        return 12
    if "11" in text_lower or "eleventh" in text_lower or "+1" in text_lower:
        return 11
    if "10" in text_lower or "tenth" in text_lower or "sslc" in text_lower:
        return 10
    if "college" in text_lower or "degree" in text_lower or "diploma" in text_lower:
        return 12
    return None

def parse_category(text: str) -> Optional[str]:
    text_upper = text.upper()
    for cat in ["MBC", "DNC", "SC", "ST", "BC", "OC", "GENERAL"]:
        if re.search(r'\b' + cat + r'\b', text_upper):
            return "General" if cat in ["OC", "GENERAL"] else cat
    if "backward" in text.lower():
        return "BC"
    if "most backward" in text.lower():
        return "MBC"
    if "scheduled caste" in text.lower() or "dalit" in text.lower():
        return "SC"
    if "scheduled tribe" in text.lower() or "tribal" in text.lower():
        return "ST"
    return None

def parse_gender(text: str) -> Optional[str]:
    t = text.lower()
    if any(w in t for w in ["girl", "female", "woman", "daughter", "she", "பெண்"]):
        return "female"
    if any(w in t for w in ["boy", "male", "man", "son", "he", "ஆண்"]):
        return "male"
    return None

def process_intake_message(session_id: str, message: Optional[str] = None, menu_choice: Optional[int] = None, field_updates: Optional[Dict[str, Any]] = None, language: str = "en") -> Dict[str, Any]:
    session = get_or_create_session(session_id)
    profile = session["profile"]

    # Manual field updates if sent by UI
    if field_updates:
        for k, v in field_updates.items():
            if v is not None:
                profile[k] = v

    text = (message or "").strip()

    # Process menu choices according to current step
    step = session["step"]
    if menu_choice is not None:
        if step == "class":
            mapping = {1: 10, 2: 11, 3: 12, 4: 12}
            profile["completed_class"] = mapping.get(menu_choice, 10)
        elif step == "gender":
            profile["gender"] = "female" if menu_choice == 1 else "male"
        elif step == "income":
            mapping = {1: 90000, 2: 180000, 3: 240000, 4: 400000, 5: 750000}
            profile["income"] = mapping.get(menu_choice, 150000)
        elif step == "category":
            mapping = {1: "BC", 2: "MBC", 3: "SC", 4: "ST", 5: "General"}
            profile["category"] = mapping.get(menu_choice, "BC")
        elif step == "confirm":
            if menu_choice == 1:
                profile["confirmed"] = True
            elif menu_choice == 2:
                profile["confirmed"] = False
                profile["completed_class"] = None
                session["step"] = "class"
        elif menu_choice == 101:
            profile["confirmed"] = False
            profile["completed_class"] = None
            session["step"] = "class"

    # Natural language parsing on message
    if text:
        # Check if user says reset
        if text.lower() in ["reset", "restart", "start over"]:
            session["profile"] = {
                "name": "Student",
                "state": "Tamil Nadu",
                "completed_class": None,
                "income": None,
                "category": None,
                "gender": None,
                "course_pursuing": None,
                "confirmed": False
            }
            session["step"] = "class"
            profile = session["profile"]

        # Confirm intent when in confirmation step
        if step == "confirm" and any(w in text.lower() for w in ["yes", "confirm", "correct", "right", "schemes", "sure", "ok", "fine", "ஆம்", "சரி"]):
            profile["confirmed"] = True

        # Extract whatever is present in message
        c = parse_class(text)
        if c: profile["completed_class"] = c
        
        g = parse_gender(text)
        if g: profile["gender"] = g
        
        inc = parse_income(text)
        if inc: profile["income"] = inc
        
        cat = parse_category(text)
        if cat: profile["category"] = cat

        if "tamil nadu" in text.lower() or "tamilnadu" in text.lower() or "tn" in text.lower():
            profile["state"] = "Tamil Nadu"

    # Identify missing fields in priority order
    missing = []
    if profile.get("completed_class") is None: missing.append("completed_class")
    if profile.get("gender") is None: missing.append("gender")
    if profile.get("income") is None: missing.append("income")
    if profile.get("category") is None: missing.append("category")

    # Generate reply and options based on next missing field
    if "completed_class" in missing:
        session["step"] = "class"
        reply = "Vanakkam! Welcome to SETU. What is the student's highest completed education level?"
        reply_ta = "வணக்கம்! சேது (SETU) தளத்திற்கு வரவேற்கிறோம். மாணவர் முடித்த கல்வி தகுதி என்ன?"
        options = [
            {"id": 1, "label": "Completed 10th (SSLC)", "label_ta": "10-ம் வகுப்பு முடித்தவர்"},
            {"id": 2, "label": "Completed 11th (+1)", "label_ta": "11-ம் வகுப்பு முடித்தவர்"},
            {"id": 3, "label": "Completed 12th (HSC / +2)", "label_ta": "12-ம் வகுப்பு முடித்தவர்"},
            {"id": 4, "label": "Entering College / Diploma", "label_ta": "கல்லூரி / டிப்ளமோ சேருபவர்"}
        ]
        next_q = "Please select completed standard (1-4) or speak/type."
        next_q_ta = "முடித்த வகுப்பைத் தேர்ந்தெடுக்கவும் (1-4) அல்லது கூறவும்."

    elif "gender" in missing:
        session["step"] = "gender"
        reply = "Got it! Is the applicant female or male? (Several special welfare schemes like Pudhumai Penn & Pragati are dedicated to girl students)."
        reply_ta = "சரி! விண்ணப்பதாரர் மாணவியா அல்லது மாணவரா? (புதுமைப் பெண், பிரகதி போன்ற சிறப்பு திட்டங்கள் மாணவிகளுக்கானவை)."
        options = [
            {"id": 1, "label": "Female / Girl Student", "label_ta": "மாணவி (பெண்)"},
            {"id": 2, "label": "Male / Boy Student", "label_ta": "மாணவர் (ஆண்)"}
        ]
        next_q = "Select gender to unlock targeted grants."
        next_q_ta = "பாலினத்தைத் தேர்ந்தெடுக்கவும்."

    elif "income" in missing:
        session["step"] = "income"
        reply = "What is your approximate annual family income? (Most government scholarships require annual income under ₹2.5 Lakhs)."
        reply_ta = "உங்கள் குடும்பத்தின் தோராயமான ஆண்டு வருமானம் என்ன? (பெரும்பாலான கல்வி உதவித்தொகைகளுக்கு ஆண்டு வருமானம் ₹2.5 லட்சத்திற்குள் இருக்க வேண்டும்)."
        options = [
            {"id": 1, "label": "Below ₹1,00,000 / year", "label_ta": "₹1,00,000-க்கு கீழ்"},
            {"id": 2, "label": "₹1,00,000 - ₹2,00,000", "label_ta": "₹1,00,000 முதல் ₹2,00,000"},
            {"id": 3, "label": "₹2,00,000 - ₹2,50,000", "label_ta": "₹2,00,000 முதல் ₹2,50,000"},
            {"id": 4, "label": "₹2,50,000 - ₹5,00,000", "label_ta": "₹2,50,000 முதல் ₹5,00,000"},
            {"id": 5, "label": "Above ₹5,00,000", "label_ta": "₹5,00,000-க்கு மேல்"}
        ]
        next_q = "Select annual income band or type exact amount."
        next_q_ta = "வருமான வரம்பைத் தேர்ந்தெடுக்கவும்."

    elif "category" in missing:
        session["step"] = "category"
        reply = "What is your community / social category? (Tamil Nadu welfare departments provide fee waivers based on community reservation)."
        reply_ta = "உங்கள் சமூகப் பிரிவு (Community Category) என்ன? (தமிழ்நாடு அரசு சமூகப் பிரிவு அடிப்படையில் கட்டண விலக்கு அளிக்கிறது)."
        options = [
            {"id": 1, "label": "BC (Backward Class)", "label_ta": "BC (பிற்படுத்தப்பட்டோர்)"},
            {"id": 2, "label": "MBC / DNC", "label_ta": "MBC / DNC (மிகவும் பிற்படுத்தப்பட்டோர்)"},
            {"id": 3, "label": "SC (Scheduled Caste)", "label_ta": "SC (ஆதிதிராவிடர்)"},
            {"id": 4, "label": "ST (Scheduled Tribe)", "label_ta": "ST (பழங்குடியினர்)"},
            {"id": 5, "label": "General / OC", "label_ta": "General / OC (பொதுப்பிரிவு)"}
        ]
        next_q = "Select community category."
        next_q_ta = "சமூகப் பிரிவைத் தேர்ந்தெடுக்கவும்."

    elif profile.get("confirmed"):
        # Profile is fully confirmed -> execute eligibility and return matched schemes
        session["step"] = "matched"
        all_matches = evaluate_eligibility(profile)
        eligible_schemes = [s for s in all_matches if s["eligible"]]
        count = len(eligible_schemes)
        reply = (
            f"🎉 Profile confirmed! We evaluated your profile against all active government welfare schemes.\n\n"
            f"You are eligible for {count} government scholarship scheme{'s' if count != 1 else ''}! "
            f"Click any scheme below to visit its verified official portal directly or start your application guidance checklist."
        )
        reply_ta = (
            f"🎉 உங்கள் விவரங்கள் உறுதிசெய்யப்பட்டன! மத்திய மற்றும் மாநில அரசின் திட்டங்களுடன் ஒப்பிட்டு சரிபார்க்கப்பட்டது.\n\n"
            f"நீங்கள் {count} அரசு உதவித்தொகை திட்டங்களுக்கு தகுதி பெற்றுள்ளீர்கள்! "
            f"அதிகாரப்பூர்வ இணையதளத்தை பார்வையிட அல்லது விண்ணப்ப வழிகாட்டலைத் தொடங்க கீழே உள்ள திட்டங்களைப் பயன்படுத்தவும்."
        )
        options = [
            {"id": 100, "label": "📋 View Full Schemes Comparison", "label_ta": "📋 அனைத்து திட்டங்களையும் காண்க"},
            {"id": 101, "label": "🔄 Edit Profile Details", "label_ta": "🔄 விவரங்களை மாற்றுக"}
        ]
        next_q = "Select a scheme to view details or visit official portal."
        next_q_ta = "திட்டத்தை தேர்வு செய்து விவரங்களை அறியவும்."

        return {
            "session_id": session_id,
            "reply": reply,
            "reply_ta": reply_ta,
            "profile": profile,
            "missing_fields": [],
            "next_question": next_q,
            "next_question_ta": next_q_ta,
            "menu_options": options,
            "is_complete": True,
            "ready_for_confirmation": False,
            "matched_schemes": eligible_schemes
        }

    else:
        # All required fields are present but not yet confirmed
        session["step"] = "confirm"
        inc_formatted = f"₹ {profile['income']:,}" if profile.get('income') else "Not specified"
        reply = f"Great! Profile summary:\n• Education: Class {profile['completed_class']}\n• State: {profile['state']}\n• Gender: {profile['gender'].capitalize()}\n• Family Income: {inc_formatted}\n• Community: {profile['category']}\n\nIs this accurate?"
        reply_ta = f"அருமை! விவரச் சுருக்கம்:\n• கல்வி: வகுப்பு {profile['completed_class']}\n• மாநிலம்: {profile['state']}\n• பாலினம்: {profile['gender']}\n• ஆண்டு வருமானம்: {inc_formatted}\n• சமூகப்பிரிவு: {profile['category']}\n\nஇந்தத் தகவல்கள் சரியானவையா?"
        options = [
            {"id": 1, "label": "1) Yes, Confirm & Find Eligible Schemes", "label_ta": "1) ஆம், சரிபார்க்கப்பட்டு திட்டங்களை காண்க"},
            {"id": 2, "label": "2) No, Change Details", "label_ta": "2) இல்லை, திருத்தம் செய்"}
        ]
        next_q = "Confirm to execute deterministic eligibility rules."
        next_q_ta = "உதவித்தொகை தகுதியை சரிபார்க்க உறுதிப்படுத்தவும்."

    return {
        "session_id": session_id,
        "reply": reply,
        "reply_ta": reply_ta,
        "profile": profile,
        "missing_fields": missing,
        "next_question": next_q,
        "next_question_ta": next_q_ta,
        "menu_options": options,
        "is_complete": len(missing) == 0,
        "ready_for_confirmation": len(missing) == 0 and not profile.get("confirmed", False),
        "matched_schemes": None
    }
