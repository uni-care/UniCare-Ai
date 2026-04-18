# 🚀 UniCare AI Verification & Smart Recommendation Service

An automated Identity Verification and Dynamic Academic Recommendation Service built for the **UniCare** platform. This service leverages the power of **Google Gemini 2.5 Flash** to perform intelligent OCR data extraction from Egyptian academic documents and generate hyper-personalized, store-integrated recommendations for students.

## 🛠 Tech Stack
- **Framework:** FastAPI (Python)
- **AI Model:** Google GenAI SDK (Gemini 2.5 Flash - Multimodal)
- **Validation & Parsing:** Pydantic Models & Robust Regex JSON parsing
- **Environment:** Dotenv for secure API management

## ✨ Key AI Features

### 1. Intelligent OCR & Validation
- **Multimodal Processing:** Supports extracting data from both Images (JPEG/PNG) and PDF files (University IDs, Nomination Cards, Graduation Certificates).
- **Smart Classification:** Automatically classifies the user as a **Student** or **Alumni** based on contextual Egyptian document formats.
- **Automated Validation:** Applies UniCare's business rules to verify eligibility:
  - Students are automatically approved.
  - Alumni are approved only if they graduated within the last **5 years**.

### 2. 100% Dynamic Recommendation Engine
- **No Hardcoded Data:** Replaced static databases with a dynamic prompt-engineered LLM that understands any faculty or department format (e.g., "CS", "حاسبات", "تربية فنية").
- **Store Integration (Search Tags):** Translates academic majors into practical `search_tags_tools` and `search_tags_references` directly queried against the platform's e-commerce store.
- **Department-Level Granularity:** Provides hyper-specific recommendations by combining both the Faculty and the specific Department.
- **Personalized AI Tips:** Generates catchy, 1-sentence Arabic motivational career tips tailored to the user's specific field of study.

### 3. Resilient Architecture
- **Fail-Safe JSON Parsing:** Utilizes Regex to safely extract JSON payloads from LLM responses, preventing API crashes if the model outputs unexpected text.
- **Single Responsibility Principle:** Clean separation of concerns between `ai_service.py` (Strictly OCR) and `main.py` (API routing and Recommendation Engine).

## 📋 API Endpoints

### 1. `POST /verify-user`
Uploads an academic document and returns extraction & validation results.

**Parameters:**
- `user_id`: (Form) Unique identifier for the user.
- `doc_type`: (Form) Type of document (e.g., University ID, Certificate).
- `file`: (File) The document file (Image or PDF).

**Response Example:**
```json
{
  "user_id": "12345",
  "verification_status": "Approved",
  "final_data": {
    "full_name": "Montaha Ahmed",
    "university": "South Valley University",
    "faculty": "Computer and Information",
    "user_type": "student",
    "extracted_year": 2024,
    "confidence_score": 95,
    "is_valid_user": true,
    "rejection_reason": null
  }  
}
```

### 2. `GET /get-recommendations`
Provides AI-generated search tags and career tips based on the user's academic profile.

**Parameters:**
- `faculty`: (Query - Required) Name of the faculty.
department`: (Query - Optional) Specific department for higher accuracy.

**Response Example:**
```json
{
  "faculty_detected": "كلية الحاسبات والمعلومات - قسم الذكاء الاصطناعي",
  "search_tags_tools": ["لابتوب", "فلاش ميموري", "نظارة حماية"],
  "search_tags_references": ["Machine Learning", "Data Structures", "Python"],
  "ai_personalized_tip": "مستقبل التكنولوجيا بين يديك، استثمر في تعلم خوارزميات الذكاء الاصطناعي لتكون رائداً في مجالك!"
}
```
