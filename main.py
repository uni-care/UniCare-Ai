import base64
import json
import re
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, Form, Query
from google.genai import types

from ai_service import OCRService
from model import VerificationResponse, ExtractedData

app = FastAPI(title="UNICARE AI Service")
ocr_service = OCRService()


# ==========================================
# API Endpoints
# ==========================================
@app.post("/verify-user")
async def verify_user(
        user_id: str = Form(...),
        doc_type: str = Form(...),
        file: UploadFile = File(...),
):

    contents = await file.read()
    encoded = base64.b64encode(contents).decode("utf-8")
    file_data_url = f"data:{file.content_type};base64,{encoded}"

    raw_extracted_data = await ocr_service.extract_data_from_file(
        file_data_url=file_data_url,
        doc_type=doc_type
    )

    user_type = raw_extracted_data.get("user_type")
    extracted_year = raw_extracted_data.get("extracted_year")

    is_valid_user = False
    current_year = datetime.now().year

    if user_type == "student":
        is_valid_user = True
    elif user_type == "alumni":
        if extracted_year:
            years_since_grad = current_year - extracted_year
            if years_since_grad <= 5:
                is_valid_user = True

    return {
        "university": raw_extracted_data.get("university"),
        "faculty": raw_extracted_data.get("faculty"),
        "is_approved": is_valid_user
    }


@app.get("/get-recommendations")
async def generate_smart_recommendations(faculty_name: str, department_name: str = None):
    if not faculty_name:
        return {
            "search_tags_tools": [],
            "search_tags_references": [],
            "ai_personalized_tip": "أهلاً بك في UNICARE! استكشف المتجر الآن."
        }

    target_study = f"{faculty_name} - قسم {department_name}" if department_name else faculty_name

    prompt = f"""
    أنت مستشار أكاديمي خبير لمنصة UNICARE (متجر لبيع وتأجير الأدوات والمراجع الدراسية للجامعات المصرية).
    المدخل: "{target_study}".

    مهمتك:
    1. استنتاج التخصص الرسمي (مثل: "اسنان" تصبح "كلية طب الأسنان").
    2. تحديد 3 كلمات مفتاحية (Search Tags) للبحث عن "أدوات ومعدات" (Tools) في المتجر.
    3. تحديد 2 كلمات مفتاحية (Search Tags) للبحث عن "كتب ومراجع" (References) في المتجر.
    4. كتابة نصيحة تشجيعية جذابة (Catchy) وقصيرة جداً بالعربية.

    يجب أن يكون الرد JSON فقط بهذا الهيكل:
    {{
        "faculty_detected": "اسم الكلية الرسمي",
        "search_tags_tools": ["tag1", "tag2", "tag3"],
        "search_tags_references": ["tag1", "tag2"],
        "ai_personalized_tip": "النصيحة هنا"
    }}
    """

    try:
        response = ocr_service.client.models.generate_content(
            model=ocr_service.MODEL_ID,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.8
            )
        )

        print("\n=== RAW GEMINI RESPONSE ===")
        print(response.text)
        print("===========================\n")

        clean_json_text = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_json_text)

    except Exception as e:
        print(f"\n[CRITICAL ERROR]: {type(e).__name__} - {e}\n")
        return {
            "faculty_detected": faculty_name,
            "search_tags_tools": [],
            "search_tags_references": [],
            "ai_personalized_tip": "بالتوفيق في رحلتك الدراسية! تصفح قسم الأدوات والمراجع الآن."
        }