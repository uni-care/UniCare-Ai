import os
import json
import base64
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()


class OCRService:
    def __init__(self):
        # 1. Extract the Gemini API key from the environment variables
        gemini_key = os.getenv("GEMINI_API_KEY")
        if not gemini_key:
            print("⚠️ WARNING: GEMINI_API_KEY not found in the .env file")

        # 2. Initialize the Gemini client using the new official SDK
        self.client = genai.Client(api_key=gemini_key)

        # Define the model to be used (Gemini 2.5 Flash is currently the fastest and most cost-effective for multimodal tasks)
        self.MODEL_ID = 'gemini-2.5-flash'

    # Accepts a base64 data URL representing either an image or a PDF document
    async def extract_data_from_file(self, file_data_url: str, doc_type: str) -> dict:

        # Note: The prompt is kept in Arabic to optimize the model's accuracy
        # when reading and extracting data from Egyptian academic documents.
        prompt = f"""
        أنت مساعد ذكي مخصص لمنصة UNICARE. مهمتك قراءة (صورة أو ملف PDF) لمستند إثبات قيد أو تخرج مصري من نوع ({doc_type}).

        المستند قد يكون:
        1. بطاقة ترشيح (Nomination Card): طالب جديد.
        2. كارنيه جامعة (University ID): طالب حالي.
        3. ظهر بطاقة رقم قومي (National ID): ابحث في خانة المهنة.
        4. شهادة تخرج أو كارنيه نقابة: خريج.

        مطلوب إرجاع البيانات بصيغة JSON Object فقط بالهيكل التالي بدقة:
        {{
            "full_name": "اسم الشخص بالكامل كما هو مكتوب",
            "university": "اسم الجامعة",
            "faculty": "اسم الكلية",
            "user_type": "student" أو "alumni" أو "unknown",
            "extracted_year": سنة التخرج للخريج، أو آخر سنة دراسية للطالب (مثل 2023). إذا لم تجد أي سنة، ضع null,
            "confidence_score": 95
        }}

        تعليمات التحديد (user_type) - ركز جداً:
        - "student": بمجرد رؤيتك لكارنيه جامعة، أو بطاقة ترشيح، أو كلمة "طالب/طالبة" في البطاقة.
        - "alumni": إذا كانت المهنة "حاصل على"، "مهندس"، "طبيب"، أو المستند شهادة تخرج.
        - افصل اسم الكلية عن الجامعة بذكاء.
        """

        try:
            # 3. Extract the MIME type and the base64 encoded data from the Data URL
            # Example parsing: "data:application/pdf;base64,JVBERi..." -> "application/pdf" and "JVBERi..."
            header, encoded_data = file_data_url.split(",", 1)
            mime_type = header.split(":")[1].split(";")[0]

            # Decode the base64 string into raw bytes
            file_bytes = base64.b64decode(encoded_data)

            # 4. Prepare the document part for the Gemini API
            # The model automatically processes PDFs or images correctly based on the provided mime_type
            document_part = types.Part.from_bytes(
                data=file_bytes,
                mime_type=mime_type
            )

            # 5. Send the request to the model, enforcing a JSON response format
            response = self.client.models.generate_content(
                model=self.MODEL_ID,
                contents=[prompt, document_part],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.1,  # Low temperature ensures factual and deterministic extraction
                )
            )

            # 6. Clean the response to prevent JSON parsing errors
            # (Removes Markdown code blocks if the model accidentally includes them)
            result_text = response.text
            clean_json_text = result_text.replace("```json", "").replace("```", "").strip()

            return json.loads(clean_json_text)

        except Exception as e:
            print(f"[OCR Error]: {e}")
            return {"user_type": "unknown", "error_message": str(e)}