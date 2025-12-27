from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
import os
import random
from datetime import datetime

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)

SHEETBEST_URL = os.getenv("SHEETBEST_URL")

def get_meta(prefix="ID"):
    return {
        "id": f"{prefix}-{random.randint(10000, 99999)}",
        "date": datetime.now().strftime("%Y-%m-%d %H:%M")
    }

@app.get("/api/cert/{cert_id}")
def check_cert(cert_id: str):
    if not SHEETBEST_URL: raise HTTPException(status_code=500, detail="Config missing")
    res = requests.get(f"{SHEETBEST_URL}/tabs/Certificates/search?ID={cert_id}").json()
    if not res: return {"status": "not_found"}
    
    cert = res[0]
    expired = False
    if cert.get("ExpDate"):
        try:
            if datetime.now() > datetime.strptime(cert["ExpDate"], "%Y-%m-%d"):
                expired = True
        except: pass
    return {"status": "success", "expired": expired, "data": cert}

@app.post("/api/members/req")
def member_req(data: dict):
    meta = get_meta("MEM")
    payload = {**data, "ID": meta["id"], "Date": meta["date"]}
    requests.post(f"{SHEETBEST_URL}/tabs/MembersReq", json=payload)
    return {"id": meta["id"]}

@app.get("/api/members/points/{sid}")
def points(sid: str):
    res = requests.get(f"{SHEETBEST_URL}/tabs/Members/search?StudentID={sid}").json()
    if res:
        return {"name": res[0].get("NameFa"), "points": res[0].get("Points"), "link": res[0].get("Link")}
    return {"status": "not_found"}

@app.post("/api/submit/{target}")
def submit_all(target: str, data: dict):
    tabs = {"associations": "Assosiations", "teachers": "Teachers", "companies": "Companies", "suggestions": "Suggestions", "organize": "OrganizeReq"}
    sheet = tabs.get(target)
    if not sheet: raise HTTPException(status_code=404)
    meta = get_meta(target[:2].upper())
    payload = {**data, "ID": meta["id"], "Date": meta["date"]}
    requests.post(f"{SHEETBEST_URL}/tabs/{sheet}", json=payload)
    return {"id": meta["id"]}
