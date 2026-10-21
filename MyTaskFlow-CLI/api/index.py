import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google import genai
from google.genai import types

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PlanRequest(BaseModel):
    raw_tasks: str
    target_date: str

@app.post("/api/generate-plan")
def generate_plan(req: PlanRequest):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY environment variable is missing on server.")

    client = genai.Client(api_key=api_key)

    prompt = f"""
    You are MyTaskFlow AI, an elite productivity assistant.
    Organize these raw tasks/thoughts into an optimal schedule for {req.target_date}.
    
    Raw Input:
    {req.raw_tasks}
    
    Output structured JSON format strictly following this schema:
    {{
      "schedule_date": "{req.target_date}",
      "top_3_priorities": ["Priority 1", "Priority 2", "Priority 3"],
      "productivity_quote": "A short motivational quote for the day",
      "schedule": [
        {{
          "id": 1,
          "time_slot": "09:00 AM - 10:00 AM",
          "task": "Task name",
          "priority": "High",
          "category": "Work",
          "quick_tip": "Actionable tip to complete efficiently",
          "completed": false
        }}
      ]
    }}
    """

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        return json.loads(response.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
