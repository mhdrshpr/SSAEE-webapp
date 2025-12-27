from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import requests
import os
import random
from datetime import datetime

app = FastAPI(title="SAEE Backend API")

# --- تنظیمات CORS برای ارتباط با فرانت‌اِند ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# آدرس API شیت‌بست (در پنل Render در بخش Environment Variables با نام SHEETBEST_URL ست کنید)
SHEET_URL = os.getenv("SHEETBEST_URL")

# تابع کمکی برای گرفتن تاریخ و زمان شمسی/میلادی فعلی برای ثبت در شیت
def get_now():
    return datetime.now().strftime("%Y-%m-%d %H:%M")

# --- سرو کردن فایل اصلی وب‌اپلیکیشن ---
@app.get("/")
async def serve_index():
    return FileResponse("index.html")

# --- ۱. استعلام گواهینامه (GET) ---
@app.get("/api/cert/{cert_id}")
def check_cert(cert_id: str):
    if not SHEET_URL:
        raise HTTPException(status_code=500, detail="Sheet URL not configured")
    
    try:
        # جستجو در تب Certificates
        response = requests.get(f"{SHEET_URL}/tabs/Certificates/search?ID={cert_id}")
        res = response.json()
        
        if not res or len(res) == 0:
            return {"status": "not_found"}
        
        cert = res[0]
        cert_status = "valid" # وضعیت پیش‌فرض
        
        # بررسی تاریخ انقضا (فرمت ستون ExpDate باید YYYY-MM-DD باشد)
        if cert.get("ExpDate"):
            try:
                exp_date = datetime.strptime(cert["ExpDate"], "%Y-%m-%d")
                if datetime.now() > exp_date:
                    cert_status = "expired"
            except:
                pass # اگر فرمت تاریخ غلط بود، همان معتبر در نظر گرفته می‌شود
            
        return {
            "status": "success",
            "cert_status": cert_status,
            "data": cert
        }
    except Exception as e:
        print(f"Error in CheckCert: {e}")
        return {"status": "error", "message": str(e)}

# --- ۲. ثبت درخواست عضویت (POST) ---
@app.post("/api/members/req")
def member_request(data: dict):
    new_id = f"MEM-{random.randint(1000, 9999)}"
    payload = {
        "ID": new_id,
        "Date": get_now(),
        "Name": data.get("Name"),
        "NationalID": data.get("NationalID"),
        "StudentID": data.get("StudentID")
    }
    try:
        requests.post(f"{SHEET_URL}/tabs/MembersReq", json=payload)
        return {"status": "success", "id": new_id}
    except:
        raise HTTPException(status_code=500, detail="Failed to write to sheet")

# --- ۳. دریافت اطلاعات امتیاز اعضا (GET) ---
@app.get("/api/members/info/{sid}")
def get_member_info(sid: str):
    try:
        res = requests.get(f"{SHEET_URL}/tabs/Members/search?StudentID={sid}").json()
        if not res or len(res) == 0:
            return {"status": "not_found"}
        return {"status": "success", "data": res[0]}
    except:
        return {"status": "error"}

# --- ۴. ارسال پیشنهادات و سایر فرم‌ها (POST) ---
@app.post("/api/submit/{target}")
def submit_collab(target: str, data: dict):
    # نقشه‌برداری از نام‌های فرانت‌اِند به تب‌های گوگل‌شیت
    tab_map = {
        "associations": "Associations",
        "teachers": "Teachers",
        "companies": "Companies",
        "suggestions": "Suggestions"
    }
    sheet_name = tab_map.get(target)
    if not sheet_name:
        raise HTTPException(status_code=404, detail="Target tab not found")
    
    prefix = target[:2].upper()
    new_id = f"{prefix}-{random.randint(1000, 9999)}"
    
    payload = {
        "ID": new_id,
        "Date": get_now(),
        **data # شامل فیلدهای ارسالی از فرم (Call, Subject, Note)
    }
    
    try:
        requests.post(f"{SHEET_URL}/tabs/{sheet_name}", json=payload)
        return {"status": "success", "id": new_id}
    except:
        return {"status": "error"}

# --- ۵. درخواست ارتقا/تمدید (PUT/PATCH) ---
@app.put("/api/members/upgrade/{sid}")
def request_upgrade(sid: str):
    try:
        # آپدیت ستون UpReq در شیت Members برای ردیفی که StudentID آن مطابقت دارد
        requests.patch(f"{SHEET_URL}/tabs/Members/StudentID/{sid}", json={"UpReq": "TRUE"})
        return {"status": "success"}
    except:
        return {"status": "error"}
