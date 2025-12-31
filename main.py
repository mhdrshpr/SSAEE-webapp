from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import requests
import os
import random
from datetime import datetime
from fastapi.staticfiles import StaticFiles

app = FastAPI()
app.mount("/static", StaticFiles(directory="."), name="static")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

SHEET_URL = os.getenv("SHEETBEST_URL")

def get_now():
    return datetime.now().strftime("%Y-%m-%d")
from fastapi.responses import FileResponse

@app.get("/logo.png")
async def get_logo():
    file_path = os.path.join("static", "logo.png") 
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return {"error": "File not found in static folder"}

# --- بخش گواهی ---
@app.get("/api/cert/{cert_id}")
def check_cert(cert_id: str):
    res = requests.get(f"{SHEET_URL}/tabs/Certificates/search?ID={cert_id}").json()
    if not res: return {"status": "not_found"}
    cert = res[0]
    status = "valid"
    
    if cert.get("ExpDate"):
        try:
            exp_date = datetime.strptime(cert["ExpDate"], "%m/%d/%Y")
            if datetime.now() > exp_date:
                status = "expired"
        except Exception:
            pass  
    return {"status": "success", "cert_status": status, "data": cert}
    
@app.get("/api/cert/download/{cert_id}")
def download_cert(cert_id: str):
    res = requests.get(f"{SHEET_URL}/tabs/Certificates/search?ID={cert_id}").json()
    if not res or not res[0].get("Link"): raise HTTPException(status_code=404)
    return {"link": res[0]["Link"]}

# --- بخش اعضا ---
@app.post("/api/members/req")
def member_req(data: dict):
    new_id = f"MEM-{random.randint(1000, 9999)}"
    payload = {**data, "ID": new_id, "Date": get_now()}
    response = requests.post(f"{SHEET_URL}/tabs/MembersReq", json=payload)
    
    if response.status_code == 201 or response.status_code == 200:
        return {"id": new_id}
    else:
        raise HTTPException(status_code=500, detail="خطا در پردازش اطلاعات")

@app.get("/api/members/card/{sid}")
def get_card(sid: str):
    res = requests.get(f"{SHEET_URL}/tabs/Members/search?StudentID={sid}").json()
    if not res or not res[0].get("Link"): return {"status": "not_found"}
    return {"link": res[0]["Link"]}

@app.patch("/api/members/upgrade/{id}")
def member_upgrade(id: str):
    try:
        search_url = f"{SHEET_URL}/tabs/Members/search?StudentID={id}"
        response = requests.get(search_url)
        data = response.json()

        if not data or not isinstance(data, list) or len(data) == 0:
            return {"status": "error", "code": "NOT_FOUND"}

        user = data[0]

        is_already_true = str(user.get("UpgradeReq", "")).upper() == "TRUE"
        
        if is_already_true:
            return {"status": "error", "code": "ALREADY_EXISTS"}

        update_url = f"{SHEET_URL}/tabs/Members/StudentID/{id}"
        upd_res = requests.patch(update_url, json={"UpgradeReq": "TRUE"})

        if upd_res.status_code in [200, 201]:
            return {"status": "success"}
        else:
            return {"status": "error", "code": "UPDATE_FAILED"}

    except Exception as e:
        return {"status": "error", "code": "SYSTEM_ERROR", "detail": str(e)}
        
@app.get("/api/members/points/{sid}")
def get_points(sid: str):
    res = requests.get(f"{SHEET_URL}/tabs/Members/search?StudentID={sid}").json()
    if not res: return {"status": "not_found"}
    return {"name": res[0].get("NameFa"), "points": res[0].get("Points")}

# --- بخش همکاری و کارگاه ---

@app.post("/api/collab/associations")
def association_req(data: dict):
    new_id = f"ASC-{random.randint(1000, 9999)}"
    
    payload = {
        "Name": data.get("Name"),
        "University": data.get("University"),
        "Field": data.get("Field"),
        "Course": data.get("Course"),
        "Phone": data.get("Phone"),
        "ID": new_id,
        "Date": get_now()
    }
    
    try:
        url = f"{SHEET_URL}/tabs/Associations"
        res = requests.post(url, json=[payload]) 
        
        if res.status_code in [200, 201]:
            return {"status": "success", "id": new_id}
        else:
            print(f"SheetBest Error: {res.status_code} - {res.text}")
            return {"status": "error", "message": res.text}
    except Exception as e:
        print(f"System Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
        
@app.get("/")
async def serve_index(): return FileResponse("index.html")
