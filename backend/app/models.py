from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class StudentProfile(BaseModel):
    student_id: Optional[str] = None
    name: Optional[str] = "Student"
    state: str = "Tamil Nadu"
    completed_class: int = Field(..., description="Completed school class, e.g. 10, 11, 12, or 13 for Diploma/UG")
    income: int = Field(..., description="Annual family income in INR")
    category: str = Field("General", description="Community/Category: OC, BC, MBC, DNC, SC, ST, etc.")
    gender: str = Field("any", description="male, female, other, any")
    course_pursuing: Optional[str] = None
    language: str = "en"
    confirmed: bool = False

class SchemeCondition(BaseModel):
    field: str
    description: str
    met: bool
    details: Optional[str] = None

class SchemeMatchResult(BaseModel):
    scheme_id: str
    name: str
    name_ta: Optional[str] = None
    state: str
    eligible: bool
    conditions: List[SchemeCondition]
    benefit_amount: str
    benefit_amount_ta: Optional[str] = None
    deadline: str
    documents: List[str]
    apply_steps: List[str]
    official_url: str
    source_authority: str
    last_verified: str
    status: str

class CaseRecord(BaseModel):
    case_id: str
    student_name: str
    phone: Optional[str] = "9876543210"
    state: str
    scheme_id: str
    scheme_name: str
    status: str = "MATCHED"  # MATCHED, DOCUMENTS_PENDING, DOCUMENTS_READY, APPLIED, STUCK, COMPLETED
    days_inactive: int = 0
    teacher_alert: bool = False
    reminder_sent: bool = False
    notes: Optional[str] = None
    created_at: str
    updated_at: str

class IntakeRequest(BaseModel):
    session_id: Optional[str] = "default"
    message: Optional[str] = None
    menu_choice: Optional[int] = None
    field_updates: Optional[Dict[str, Any]] = None
    language: str = "en"

class IntakeResponse(BaseModel):
    session_id: str
    reply: str
    reply_ta: str
    profile: Dict[str, Any]
    missing_fields: List[str]
    next_question: Optional[str] = None
    next_question_ta: Optional[str] = None
    menu_options: Optional[List[Dict[str, Any]]] = None
    is_complete: bool = False
    ready_for_confirmation: bool = False
    matched_schemes: Optional[List[Dict[str, Any]]] = None
