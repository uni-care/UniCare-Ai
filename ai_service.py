import os
import json
import base64
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

class OCRService:
    def __init__(self):
        gemini_key = os.getenv("GEMINI_API_KEY")
        if not gemini_key:
            print("⚠️ WARNING: GEMINI_API_KEY not found in the .env file")

        self.client = genai.Client(api_key=gemini_key)
        self.MODEL_ID = 'gemini-2.5-flash'

    async def verify_academic_id(self, image_data: str) -> dict:
        prompt = (
            "أنت خبير في تدقيق الهويات الأكاديمية. قم بفحص الصورة واستخرج البيانات التالية بصيغة JSON فقط: "
            "1. university (اسم الجامعة) "
            "2. faculty (اسم الكلية) "
            "3. is_approved (true إذا كان كارنيه جامعة حقيقي وواضح، false خلاف ذلك) "
            "الرد يجب أن يكون JSON فقط كالتالي: "
            '{"university": "string", "faculty": "string", "is_approved": boolean}'
        )

        response = await self.client.chat.completions.create(
            model=self.DEFAULT_MODEL,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": image_data}},
                ],
            }],
            response_format={"type": "json_object"},
        )
        return json.loads(response.choices[0].message.content)