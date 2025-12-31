from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import requests
import os
import random
from datetime import datetime

app = FastAPI()

# تنظیمات استاتیک و کورز
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

@app.get("/")
async def serve_index():
    return FileResponse("index.html")

@app.get("/logo.png")
async def get_logo():
    file_path = os.path.join("static", "logo.png") 
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return {"error": "File not found"}

# --- بخش گواهی ---
@app.get("/api/cert/{cert_id}")
def check_cert(cert_id: str):
    try:
        res = requests.get(f"{SHEET_URL}/tabs/Certificates/search?ID={cert_id}").json()
        if not res: 
            return {"status": "not_found"}
        
        cert = res[0]
        status = "valid"
        
        if cert.get("ExpDate"):
            try:
                exp_date = datetime.strptime(cert["ExpDate"], "%m/%d/%Y")
                if datetime.now() > exp_date:
                    status = "expired"
            except:
                pass  
        return {"status": "success", "cert_status": status, "data": cert}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/cert/download/{cert_id}")
def download_cert(cert_id: str):
    try:
        res = requests.get(f"{SHEET_URL}/tabs/Certificates/search?ID={cert_id}").json()
        if not res or not res[0].get("Link"): 
            raise HTTPException(status_code=404)
        return {"link": res[0]["Link"]}
    except:
        raise HTTPException(status_code=404)

# --- بخش اعضا ---
@app.post("/api/members/req")
def member_req(data: dict):
    new_id = f"MEM-{random.randint(1000, 9999)}"
    # ارسال به صورت لیست برای پایداری در Sheet.best
    payload = [{**data, "ID": new_id, "Date": get_now()}]
    
    response = requests.post(f"{SHEET_URL}/tabs/MembersReq", json=payload)
    
    if response.status_code in [200, 201]:
        return {"id": new_id}
    else:
        print(f"Member Req Error: {response.text}")
        raise HTTPException(status_code=500, detail="خطا در ثبت عضویت")

@app.get("/api/members/card/{sid}")
def get_card(sid: str):
    try:
        res = requests.get(f"{SHEET_URL}/tabs/Members/search?StudentID={sid}").json()
        if not res or not res[0].get("Link"): 
            return {"status": "not_found"}
        return {"link": res[0]["Link"]}
    except:
        return {"status": "error"}

@app.patch("/api/members/upgrade/{id}")
def member_upgrade(id: str):
    try:
        search_url = f"{SHEET_URL}/tabs/Members/search?StudentID={id}"
        data = requests.get(search_url).json()

        if not data or len(data) == 0:
            return {"status": "error", "code": "NOT_FOUND"}

        user = data[0]
        if str(user.get("UpgradeReq", "")).upper() == "TRUE":
            return {"status": "error", "code": "ALREADY_EXISTS"}

        update_url = f"{SHEET_URL}/tabs/Members/StudentID/{id}"
        upd_res = requests.patch(update_url, json={"UpgradeReq": "TRUE"})

        if upd_res.status_code in [200, 201]:
            return {"status": "success"}
        return {"status": "error", "code": "UPDATE_FAILED"}
    except Exception as e:
        return {"status": "error", "code": "SYSTEM_ERROR", "detail": str(e)}

@app.get("/api/members/points/{sid}")
def get_points(sid: str):
    try:
        res = requests.get(f"{SHEET_URL}/tabs/Members/search?StudentID={sid}").json()
        if not res: 
            return {"status": "not_found"}
        return {"name": res[0].get("NameFa"), "points": res[0].get("Points")}
    except:
        return {"status": "error"}

# --- بخش همکاری  ---
@app.post("/api/collab/associations")
def association_req(data: dict):
    new_id = f"ASC-{random.randint(1000, 9999)}"
    
    payload = [{
        "Name": data.get("Name"),
        "University": data.get("University"),
        "Field": data.get("Field"),
        "Course": data.get("Course"),
        "Phone": data.get("Phone"),
        "ID": new_id,
        "Date": get_now()
    }]
    
    try:
        url = f"{SHEET_URL}/tabs/Associations"
        res = requests.post(url, json=payload) 
        
        if res.status_code in [200, 201]:
            return {"status": "success", "id": new_id}
        else:
            print(f"Sheet Error: {res.text}")
            return {"status": "error", "message": "خطای دیتابیس"}
    except Exception as e:
        print(f"System Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/collab/teachers")
def teacher_req(data: dict):
    new_id = f"TCH-{random.randint(1000, 9999)}"
    
    payload = [{
        "Name": data.get("Name"),
        "University": data.get("University"),
        "AcRank": data.get("AcRank"),
        "Course": data.get("Course"),
        "Phone": data.get("Phone"),
        "ID": new_id,
        "Date": get_now()
    }]
    
    try:
        url = f"{SHEET_URL}/tabs/Teachers"
        res = requests.post(url, json=payload)
        
        if res.status_code in [200, 201]:
            return {"status": "success", "id": new_id}
        else:
            return {"status": "error", "message": "Database Error"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/collab/companies")
def company_req(data: dict):
    new_id = f"COM-{random.randint(1000, 9999)}"
    
    payload = [{
        "Name": data.get("Name"),
        "Phone": data.get("Phone"),
        "Note": data.get("Note"),
        "ID": new_id,
        "Date": get_now()
    }]
    
    try:
        url = f"{SHEET_URL}/tabs/Companies"
        res = requests.post(url, json=payload)
        
        if res.status_code in [200, 201]:
            return {"status": "success", "id": new_id}
        else:
            return {"status": "error", "message": "Database Error"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@app.post("/api/feedback")
def feedback_req(data: dict):
    new_id = f"FDB-{random.randint(1000, 9999)}"
    
    payload = [{
        "Subject": data.get("Subject"),
        "Unit": data.get("Unit"),
        "Phone": data.get("Phone"),
        "Note": data.get("Note"),
        "ID": new_id,
        "Date": get_now()
    }]
    
    try:
        url = f"{SHEET_URL}/tabs/Suggestions"
        res = requests.post(url, json=payload)
        
        if res.status_code in [200, 201]:
            return {"status": "success", "id": new_id}
        else:
            return {"status": "error", "message": "Database Error"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/workshop/req")
def workshop_req(data: dict):
    new_id = f"WRQ-{random.randint(1000, 9999)}"
    
    payload = [{
        "Phone": data.get("Phone"),
        "Course": data.get("Course"),
        "Teacher": data.get("Teacher") if data.get("Teacher") else "نامشخص",
        "Time": data.get("Time") if data.get("Time") else "نامشخص",
        "ID": new_id,
        "Date": get_now()
    }]
    
    try:
        url = f"{SHEET_URL}/tabs/WorkshopReq"
        res = requests.post(url, json=payload)
        
        if res.status_code in [200, 201]:
            return {"status": "success", "id": new_id}
        else:
            return {"status": "error", "message": "Database Error"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/class/req")
def class_req(data: dict):
    new_id = f"CRQ-{random.randint(1000, 9999)}"
    
    payload = [{
        "Phone": data.get("Phone"),
        "Course": data.get("Course"),
        "Teacher": data.get("Teacher") if data.get("Teacher") else "نامشخص",
        "Time": data.get("Time") if data.get("Time") else "نامشخص",
        "ID": new_id,
        "Date": get_now()
    }]
    
    try:
        url = f"{SHEET_URL}/tabs/ClassReq"
        res = requests.post(url, json=payload)
        
        if res.status_code in [200, 201]:
            return {"status": "success", "id": new_id}
        else:
            return {"status": "error", "message": "Database Error"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
