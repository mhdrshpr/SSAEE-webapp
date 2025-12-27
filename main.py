from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import requests
import os
import random
from datetime import datetime

app = FastAPI()

# تنظیم CORS برای دسترسی بدون محدودیت
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# متغیر محیطی در رندر ست شود
SHEET_URL = os.getenv("SHEETBEST_URL")

def get_now():
    return datetime.now().strftime("%Y-%m-%d %H:%M")

@app.get("/")
async def serve_index():
    return FileResponse("index.html")

# --- بخش گواهی (GET) ---
@app.get("/api/cert/{cert_id}")
def check_cert(cert_id: str):
    try:
        # جستجو در شیت Certificates بر اساس ستون ID
        res = requests.get(f"{SHEET_URL}/tabs/Certificates/search?ID={cert_id}").json()
        if not res: return {"status": "not_found"}
        
        cert = res[0]
        # بررسی انقضا
        expired = False
        if cert.get("ExpDate"):
            try:
                if datetime.now() > datetime.strptime(cert["ExpDate"], "%Y-%m-%d"):
                    expired = True
            except: pass
            
        return {"status": "success", "expired": expired, "data": cert}
    except:
        raise HTTPException(status_code=500, detail="Error connecting to Sheet")

# --- بخش اعضا (POST & GET) ---
@app.post("/api/members/req")
def member_request(data: dict):
    new_id = f"MEM-{random.randint(1000, 9999)}"
    payload = {
        "Name": data.get("Name"),
        "NationalID": data.get("NationalID"),
        "StudentID": data.get("StudentID"),
        "ID": new_id,
        "Date": get_now()
    }
    requests.post(f"{SHEET_URL}/tabs/MembersReq", json=payload)
    return {"id": new_id}

@app.get("/api/members/info/{sid}")
def get_member(sid: str):
    res = requests.get(f"{SHEET_URL}/tabs/Members/search?StudentID={sid}").json()
    if not res: return {"status": "not_found"}
    return {"status": "success", "data": res[0]}

# --- همکاری و پیشنهادات (POST) ---
@app.post("/api/submit/{target}")
def submit_collab(target: str, data: dict):
    tab_map = {
        "associations": "Associations",
        "teachers": "Teachers",
        "companies": "Companies",
        "suggestions": "Suggestions"
    }
    sheet_name = tab_map.get(target)
    if not sheet_name: raise HTTPException(status_code=404)
    
    new_id = f"{target[:2].upper()}-{random.randint(1000, 9999)}"
    payload = {**data, "ID": new_id, "Date": get_now()}
    requests.post(f"{SHEET_URL}/tabs/{sheet_name}", json=payload)
    return {"id": new_id}
