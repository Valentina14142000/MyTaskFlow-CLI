import os
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def organize_tasks(raw_input):
    prompt = f"""
    You are MyTaskFlow AI, an elite productivity assistant.
    Take the following raw, unorganized tasks/thoughts and organize them into an optimal daily schedule.
    
    Raw Input:
    {raw_input}
    
    Output structured JSON format:
    {{
      "schedule": [
        {{
          "time_slot": "e.g., 09:00 AM - 10:00 AM",
          "task": "Task name",
          "priority": "High/Medium/Low",
          "category": "Work/Personal/Health/Admin",
          "quick_tip": "Actionable tip to complete efficiently"
        }}
      ],
      "top_3_priorities": ["Priority 1", "Priority 2", "Priority 3"],
      "productivity_quote": "A short motivational quote for today"
    }}
    """

    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json"
        )
    )
    return response.text

if __name__ == "__main__":
    print("=== Welcome to MyTaskFlow AI Task Organizer ===")
    print("Enter your dump of daily tasks/thoughts (type 'DONE' on a new line when finished):")
    
    lines = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line.strip().upper() == 'DONE':
            break
        lines.append(line)
        
    user_tasks = "\n".join(lines)
    
    if user_tasks.strip():
        print("\n⚡ MyTaskFlow is analyzing and structuring your day...\n")
        structured_plan = organize_tasks(user_tasks)
        
        parsed = json.loads(structured_plan)
        print(json.dumps(parsed, indent=2))
    else:
        print("No tasks entered. Exiting.")
