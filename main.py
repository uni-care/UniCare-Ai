import base64
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, Form

# Import custom models and services
from model import VerificationResponse, ExtractedData
from ai_service import OCRService

app = FastAPI(title="UNICARE AI Service")
ocr_service = OCRService()


@app.post("/verify-user", response_model=VerificationResponse)
async def verify_user(
        user_id: str = Form(...),
        doc_type: str = Form(...),
        file: UploadFile = File(...),
):
    # 1. Read the uploaded file (Image/PDF) and convert it to a Base64 Data URL
    contents = await file.read()
    encoded = base64.b64encode(contents).decode("utf-8")

    # Dynamically format the data URL using the file's actual content type (e.g., image/jpeg or application/pdf)
    file_data_url = f"data:{file.content_type};base64,{encoded}"

    # 2. Send the file data to the AI OCR service for extraction
    raw_extracted_data = await ocr_service.extract_data_from_file(
        file_data_url=file_data_url,
        doc_type=doc_type
    )

    # Extract required fields to apply validation logic
    user_type = raw_extracted_data.get("user_type")
    extracted_year = raw_extracted_data.get("extracted_year")

    is_valid_user = False
    rejection_reason = None
    current_year = datetime.now().year

    # 3. Apply UNICARE business logic and validation rules
    if user_type == "student":
        # Active students are automatically approved
        is_valid_user = True

    elif user_type == "alumni":
        if extracted_year:
            # Calculate the number of years since graduation
            years_since_grad = current_year - extracted_year

            # UNICARE policy: Only alumni who graduated within the last 5 years are allowed
            if years_since_grad <= 5:
                is_valid_user = True
            else:
                rejection_reason = f"عفواً، مر على تخرجك {years_since_grad} سنوات. المنصة مخصصة للطلاب والخريجين الجدد (بحد أقصى 5 سنوات)."
        else:
            rejection_reason = "لم نتمكن من تحديد سنة التخرج من المستند المرفق."

    else:
        # Rejection for invalid, unreadable, or unrelated documents
        rejection_reason = "المستند غير صالح لإثبات حالة الطالب أو الخريج."

    # 4. Aggregate the extracted data into the standardized Pydantic model
    final_data = ExtractedData(
        full_name=raw_extracted_data.get("full_name"),
        university=raw_extracted_data.get("university"),
        faculty=raw_extracted_data.get("faculty"),
        user_type=user_type,
        extracted_year=extracted_year,
        confidence_score=raw_extracted_data.get("confidence_score"),
        is_valid_user=is_valid_user,
        rejection_reason=rejection_reason
    )

    # 5. Return the final verification response based on the validation outcome
    return VerificationResponse(
        user_id=user_id,
        verification_status="Approved" if is_valid_user else "Rejected",
        final_data=final_data
    )