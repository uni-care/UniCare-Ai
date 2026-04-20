import json
import os
import base64
import types

import pyodbc
from datetime import datetime
from fastapi import FastAPI, HTTPException, Form, Query
from ai_service import OCRService

app = FastAPI(title="UNICARE AI Service")
ocr_service = OCRService()


def get_user_document_path(user_id: str):
    conn_str = (
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=db48621.public.databaseasp.net,1433;"
        "DATABASE=db48621;"
        "UID=db48621;"
        "PWD=g%7H=Zk2i!9W;" 
        "TrustServerCertificate=yes;"
    )

    try:
        with pyodbc.connect(conn_str) as conn:
            cursor = conn.cursor()
            query = "SELECT DocumentUrl FROM StudentVerifications WHERE UserId = ?"
            cursor.execute(query, user_id)
            row = cursor.fetchone()
            return row[0] if row else None
    except Exception as e:
        print(f"[Database Error]: {e}")
        return None


@app.post("/verify-user")
async def verify_user(
        user_id: str = Form(...),
        doc_type: str = Form(...)
):
    try:
        db_path = get_user_document_path(user_id)
        if not db_path:
            raise HTTPException(status_code=404, detail="لم يتم العثور على مستند لهذا المستخدم.")

        clean_path = db_path.replace("\\", "/").lstrip("/")
        clean_path = clean_path.replace("wwwroot/", "")

        path_options = [
            f"./wwwroot/wwwroot/{clean_path}",
            f"./wwwroot/{clean_path}",
            f"./{clean_path}"
        ]

        full_path = next((p for p in path_options if os.path.exists(p)), None)

        if not full_path:
            failed_path = os.path.abspath(path_options[0])
            raise HTTPException(status_code=404, detail=f"الملف غير موجود. البايثون بحث هنا: {failed_path}")

        with open(full_path, "rb") as f:
            file_bytes = f.read()
            encoded = base64.b64encode(file_bytes).decode("utf-8")

            ext = full_path.lower()
            mime = "application/pdf" if ext.endswith(".pdf") else "image/png" if ext.endswith(".png") else "image/jpeg"
            file_data_url = f"data:{mime};base64,{encoded}"

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
            if extracted_year and (current_year - int(extracted_year)) <= 5:
                is_valid_user = True

        return {
            "university": raw_extracted_data.get("university"),
            "faculty": raw_extracted_data.get("faculty"),
            "is_approved": is_valid_user
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"[System Error]: {str(e)}")
        raise HTTPException(status_code=500, detail=f"خطأ تقني داخلي: {str(e)}")


def get_all_store_items():
    db_server = os.getenv("DB_SERVER")
    db_name = os.getenv("DB_NAME")
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")

    conn_str = (
        "DRIVER={ODBC Driver 17 for SQL Server};"
        f"SERVER={db_server};"
        f"DATABASE={db_name};"
        f"UID={db_user};"
        f"PWD={db_password};"
        "TrustServerCertificate=yes;"
    )

    items_list = []
    try:
        with pyodbc.connect(conn_str) as conn:
            cursor = conn.cursor()
            query = "SELECT Id, Name, Description FROM dbo.Items WHERE IsAvailable = 1"
            cursor.execute(query)

            rows = cursor.fetchall()
            print(f"--- DEBUG: Found {len(rows)} items in Items table ---")

            for row in rows:
                items_list.append({
                    "item_id": str(row[0]),  # العمود Id
                    "item_name": str(row[1]),  # العمود Name
                    "description": str(row[2])  # العمود Description
                })
        return items_list
    except Exception as e:
        print(f"[Database Error]: {e}")
        return []


@app.get("/get-recommendations")
async def generate_smart_recommendations(
        faculty_name: str = Query(...),
        department_name: str = Query(None)
):
    if not faculty_name:
        return {
            "recommended_item_ids": [],
            "ai_personalized_tip": "أهلاً بك في UNICARE! استكشف المتجر الآن."
        }

    target_study = f"{faculty_name} - قسم {department_name}" if department_name else faculty_name

    available_items = get_all_store_items()

    if not available_items:
        return {
            "recommended_item_ids": [],
            "ai_personalized_tip": "جاري تحديث منتجات المتجر، تابعنا قريباً!"
        }

    items_json_string = json.dumps(available_items, ensure_ascii=False)

    prompt = f"""
    أنت مستشار أكاديمي خبير لمنصة UNICARE (متجر للطلاب).
    الطالب يدرس في التخصص التالي: "{target_study}".

    إليك قائمة بجميع المنتجات المتاحة حالياً في المتجر (كل منتج له item_id و item_name):
    {items_json_string}

    مهمتك:
    1. تحليل تخصص الطالب بدقة.
    2. اختيار أفضل وأنسب المنتجات (أدوات أو مراجع) من القائمة السابقة التي تفيد هذا الطالب تحديداً في دراسته.
    3. كتابة نصيحة تشجيعية قصيرة جداً ومخصصة لتخصصه بالعربية.

    يجب أن يكون الرد JSON فقط بهذا الهيكل:
    {{
        "recommended_item_ids": ["id1", "id2", "id3"], 
        "ai_personalized_tip": "النصيحة هنا"
    }}
    ملاحظة هامة: يجب أن تكون الـ IDs المختارة موجودة حصراً في القائمة المرفقة.
    """

    try:
        from google.genai import types

        response = await ocr_service.client.aio.models.generate_content(
            model=ocr_service.MODEL_ID,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.3
            )
        )

        clean_json_text = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_json_text)

    except Exception as e:
        print(f"\n[CRITICAL ERROR in Recommendations]: {str(e)}\n")
        return {
            "recommended_item_ids": [],
            "ai_personalized_tip": f"بالتوفيق يا دكتور! تصفح قسم الأدوات والمراجع الخاص بـ {faculty_name}."
        }