from pydantic import BaseModel
from typing import Optional

class ExtractedData(BaseModel):
    full_name: Optional[str] = None
    university: Optional[str] = None
    faculty: Optional[str] = None
    user_type: str
    extracted_year: Optional[int] = None
    confidence_score: Optional[int] = None
    is_valid_user: bool = False
    rejection_reason: Optional[str] = None
    recommendations: Optional[dict] = None

class VerificationResponse(BaseModel):
    user_id: str
    verification_status: str
    final_data: ExtractedData