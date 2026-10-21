import os
import json
from datetime import date, timedelta
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

PLANS_DIR = "plans"
os.makedirs(PLANS_DIR, exist_ok=True)

def generate_ai_schedule(raw_input, date_label):
    prompt = f"""
    You are MyTaskFlow AI, an elite productivity assistant.
    Take the following raw, unorganized tasks/thoughts and organize them into an optimal schedule for {date_label}.
    
    Raw Input:
    {raw_input}
    
    Output structured JSON format:
    {{
      "schedule_date": "{date_label}",
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
      "productivity_quote": "A short motivational quote for the day"
    }}
    """

    response = client.models.generate_content(
        model='gemini-3.8-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json"
        )
    )
    return response.text

def check_morning_reminder():
    today = date.today().isoformat()
    today_file = os.path.join(PLANS_DIR, f"plan_{today}.json")
    
    if os.path.exists(today_file):
        print("\n" + "="*60)
        print(f" 🌅 GOOD MORNING! HERE IS YOUR BRIEFING FOR TODAY ({today})")
        print("="*60 + "\n")
        
        with open(today_file, "r") as f:
            data = json.load(f)
            print(json.dumps(data, indent=2))
        print("\n" + "="*60 + "\n")
    else:
        print(f"\nℹ️ No pre-planned schedule found for today ({today}).")
        print("Tip: Run evening planning to set up tomorrow's day ahead of time!\n")

def plan_tomorrow():
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    print(f"\n🌙 === Evening Planning for Tomorrow ({tomorrow}) ===")
    print("Enter your tasks/thoughts for tomorrow (type 'DONE' on a new line when finished):\n")
    
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
        print(f"\n⚡ MyTaskFlow is structuring tomorrow's roadmap...\n")
        structured_plan = generate_ai_schedule(user_tasks, tomorrow)
        
        parsed = json.loads(structured_plan)
        
        # Save to file
        today_file = os.path.join(PLANS_DIR, f"plan_{tomorrow}.json")
        with open(today_file, "w") as f:
            json.dump(parsed, f, indent=2)
            
        print(f"✅ Successfully saved tomorrow's plan to '{today_file}'!")
        print("\nHere is your finalized plan for tomorrow:")
        print(json.dumps(parsed, indent=2))
    else:
        print("No tasks entered. Plan discarded.")

if __name__ == "__main__":
    # 1. Automatically check for today's reminder on startup
    check_morning_reminder()
    
    # 2. Ask user what they want to do next
    print("What would you like to do?")
    print("  [1] Plan tomorrow's tasks (Evening Mode)")
    print("  [2] Exit")
    
    choice = input("\nEnter choice (1 or 2): ").strip()
    if choice == '1':
        plan_tomorrow()
    else:
        print("Have a productive day!")
