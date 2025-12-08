from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import pandas as pd
from dateutil import parser
import urllib.parse

app = FastAPI()

GRAPH_ENDPOINT = "https://graph.microsoft.com/v1.0"
user_cache = {}

def get_user_details(email, headers):
    if not email: return {"name": "Unknown", "team": "Unknown"}
    if email in user_cache: return user_cache[email]
    
    url = f"{GRAPH_ENDPOINT}/users/{email}?$select=department,displayName"
    try:
        resp = requests.get(url, headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            info = {"name": data.get('displayName', email), "team": data.get('department', 'Unassigned')}
        else:
            info = {"name": email, "team": "External/Unknown"}
    except:
        info = {"name": email, "team": "Error"}
    
    user_cache[email] = info
    return info

def get_meeting_id_from_link(user_id, join_url, headers):
    # 1. Exact Match
    url = f"{GRAPH_ENDPOINT}/users/{user_id}/onlineMeetings"
    params = {"$filter": f"JoinWebUrl eq '{join_url}'"}
    resp = requests.get(url, headers=headers, params=params)
    if resp.status_code == 200 and resp.json().get('value'):
        return resp.json()['value'][0]['id']
    
    print("DEBUG: Exact match failed, trying fallback...")
    try:
        decoded = urllib.parse.unquote(join_url)
        if 'meetup-join/' in decoded:
            thread_id = decoded.split('meetup-join/')[1].split('/0?')[0]
            r2 = requests.get(url, headers=headers, params={"$top": 20})
            if r2.status_code == 200:
                for m in r2.json().get('value', []):
                    if thread_id in urllib.parse.unquote(m.get('JoinWebUrl', '')):
                        return m['id']
    except:
        pass
    return None

def get_user_id(email, headers):
    resp = requests.get(f"{GRAPH_ENDPOINT}/users/{email}", headers=headers)
    return resp.json().get('id') if resp.status_code == 200 else None

class AnalysisRequest(BaseModel):
    token: str
    start_date: str
    end_date: str
    organizer_email: str
    meeting_link: str

@app.post("/analyze")
def analyze_standup(req: AnalysisRequest):
    headers = {'Authorization': f'Bearer {req.token}', 'Content-Type': 'application/json'}
    
    organizer_id = get_user_id(req.organizer_email, headers)
    if not organizer_id: raise HTTPException(404, "Organizer not found")

    meeting_id = get_meeting_id_from_link(organizer_id, req.meeting_link, headers)
    if not meeting_id: raise HTTPException(404, "Meeting ID not found")

    reports_url = f"{GRAPH_ENDPOINT}/users/{organizer_id}/onlineMeetings/{meeting_id}/attendanceReports"
    reports_resp = requests.get(reports_url, headers=headers)
    if reports_resp.status_code != 200: return []

    all_reports = reports_resp.json().get('value', [])
    processed_data = []
    
    start_range = parser.parse(req.start_date).date()
    end_range = parser.parse(req.end_date).date()

    print(f"DEBUG: Processing {len(all_reports)} reports...")

    for report in all_reports:
        if not report.get('meetingStartDateTime'): continue
        
        meeting_dt = parser.parse(report.get('meetingStartDateTime'))
        meeting_date = meeting_dt.date()

        if not (start_range <= meeting_date <= end_range): continue
        if meeting_dt.weekday() > 4: continue

        rec_url = f"{reports_url}/{report['id']}/attendanceRecords"
        rec_resp = requests.get(rec_url, headers=headers)
        
        attendees = []
        if rec_resp.status_code == 200:
            records = rec_resp.json().get('value', [])
            
            for rec in records:
                if not isinstance(rec, dict): continue
                
                name = "Unknown"
                email = None
                
                if isinstance(rec.get('emailAddress'), str):
                    email = rec['emailAddress']
                elif isinstance(rec.get('emailAddress'), dict):
                    email = rec['emailAddress'].get('address')

                if not email:
                    name = rec.get('identity', {}).get('displayName', 'Guest')
                else:
                    details = get_user_details(email, headers)
                    name = details['name']

                is_on_time = False
                intervals = rec.get('attendanceIntervals', [])
                if isinstance(intervals, list) and len(intervals) > 0:
                    try:
                        join_times = [parser.parse(i['joinDateTime']) for i in intervals if isinstance(i, dict) and 'joinDateTime' in i]
                        if join_times:
                            first_join = min(join_times)
                            diff_min = (first_join - meeting_dt).total_seconds() / 60
                            if diff_min <= 5:
                                is_on_time = True
                    except:
                        pass 

                if email or name != "Unknown":
                    team = details['team'] if email else "Guest"
                    attendees.append({
                        "name": name,
                        "email": email,
                        "team": team,
                        "is_on_time": is_on_time 
                    })

        m_end = parser.parse(report.get('meetingEndDateTime'))
        duration = (m_end - meeting_dt).seconds / 60

        processed_data.append({
            "date": str(meeting_date),
            "duration": round(duration, 2),
            "attendees": attendees,
            "total_attendees": len(attendees)
        })

    return processed_data

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)