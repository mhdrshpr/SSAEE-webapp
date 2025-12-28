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
    requests.post(f"{SHEET_URL}/tabs/MembersReq", json=payload)
    return {"id": new_id}

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
@app.post("/api/submit/{target}")
def submit_general(target: str, data: dict):
    tab_map = {
        "associations": "Associations", "teachers": "Teachers", 
        "companies": "Companies", "suggestions": "Suggestions", "organize": "OrganizeReq"
    }
    sheet = tab_map.get(target)
    if not sheet: raise HTTPException(status_code=404)
    new_id = f"{target[:2].upper()}-{random.randint(1000, 9999)}"
    requests.post(f"{SHEET_URL}/tabs/{sheet}", json={**data, "ID": new_id, "Date": get_now()})
    return {"id": new_id}

@app.get("/")
async def serve_index(): return FileResponse("index.html")
