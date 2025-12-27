from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
import os
import random
from datetime import datetime

app = FastAPI()

# تنظیم CORS برای اجازه دسترسی مرورگر
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

SHEETBEST_URL = os.getenv("SHEETBEST_URL")

def get_meta(p):
    return {"id": f"{p}-{random.randint(1000, 9999)}", "date": datetime.now().strftime("%Y-%m-%d")}

# --- بخش گواهی ---
@app.get("/api/cert/{cert_id}")
def check_cert(cert_id: str):
    res = requests.get(f"{SHEETBEST_URL}/tabs/Certificates/search?ID={cert_id}").json()
    if not res: return {"status": "not_found"}
    cert = res[0]
    expired = False
    if cert.get("ExpDate"):
        try:
            if datetime.now() > datetime.strptime(cert["ExpDate"], "%Y-%m-%d"): expired = True
        except: pass
    return {"status": "success", "expired": expired, "data": cert}

# --- بخش اعضا ---
@app.post("/api/members/req")
def member_req(data: dict):
    meta = get_meta("MEM")
    requests.post(f"{SHEETBEST_URL}/tabs/MembersReq", json={**data, "ID": meta["id"], "Date": meta["date"]})
    return {"id": meta["id"]}

@app.get("/api/members/points/{sid}")
def points(sid: str):
    res = requests.get(f"{SHEETBEST_URL}/tabs/Members/search?StudentID={sid}").json()
    if res: return {"name": res[0].get("NameFa"), "points": res[0].get("Points"), "link": res[0].get("Link")}
    return {"status": "not_found"}

@app.put("/api/members/upgrade/{sid}")
def upgrade(sid: str):
    requests.patch(f"{SHEETBEST_URL}/tabs/Members/StudentID/{sid}", json={"UpReq": "TRUE"})
    return {"status": "done"}

# --- همکاری و سایر فرم‌ها ---
@app.post("/api/submit/{target}")
def submit_all(target: str, data: dict):
    tabs = {"associations": "Assosiations", "teachers": "Teachers", "companies": "Companies", "suggestions": "Suggestions", "organize": "OrganizeReq"}
    meta = get_meta(target[:2].upper())
    requests.post(f"{SHEETBEST_URL}/tabs/{tabs[target]}", json={**data, "ID": meta["id"], "Date": meta["date"]})
    return {"id": meta["id"]}
from fastapi.responses import FileResponse

@app.get("/")
async def read_index():
    return FileResponse('index.html')
