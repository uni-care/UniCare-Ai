from pydantic import BaseModel
from typing import Optional

class ExtractedData(BaseModel):
    # OCR extracted data and validation results
    full_name: Optional[str] = None
    university: Optional[str] = None
    faculty: Optional[str] = None
    user_type: str  # Expected: "student", "alumni", or "unknown"
    extracted_year: Optional[int] = None  # Grad year or current academic year
    confidence_score: Optional[int] = None  # AI accuracy (0-100)
    is_valid_user: bool = False  # True if user meets UNICARE rules
    rejection_reason: Optional[str] = None  # Reason for rejection, if any

class VerificationResponse(BaseModel):
    # Final API response format
    user_id: str  # Original request ID
    verification_status: str  # Expected: "Approved" or "Rejected"
    final_data: ExtractedData  # The extracted data object