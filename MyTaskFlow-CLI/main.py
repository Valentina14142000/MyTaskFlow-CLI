import os
import json
import time
import subprocess
from datetime import date, timedelta, datetime
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

PLANS_DIR = "plans"
os.makedirs(PLANS_DIR, exist_ok=True)

def play_sound():
    """Plays a native alert sound based on operating system."""
    try:
        if os.path.exists("/System/Library/Sounds/Glass.aiff"):
            subprocess.run(["afplay", "/System/Library/Sounds/Glass.aiff"], check=False)
        elif os.name == 'nt':
            import winsound
            winsound.Beep(1000, 1000)
        else:
            print("\a")
    except Exception:
        print("\a")

def generate_ai_schedule(raw_input, date_label):
    current_time_hint = datetime.now().strftime("%I:%M %p")
    prompt = f"""
    You are MyTaskFlow AI, an elite productivity assistant.
    Take the following raw, unorganized tasks/thoughts and organize them into an optimal schedule for {date_label}.
    IMPORTANT: The current time right now is {current_time_hint}. Make sure at least one task's time slot matches or starts right around {current_time_hint} so the user can test the live monitor alert immediately.
    
    Raw Input:
    {raw_input}
    
    Output structured JSON format:
    {{
      "schedule_date": "{date_label}",
      "schedule": [
        {{
          "time_slot": "{current_time_hint} - 11:00 PM",
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

    # Retry loop specifically for 503 high-demand bursts on gemini-3.8-flash
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model='gemini-3.8-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            return response.text
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"⚠️ API busy, retrying in 2 seconds... (Attempt {attempt + 1}/{max_retries})")
                time.sleep(2)
            else:
                raise e

def check_morning_reminder():
    today = date.today().isoformat()
    today_file = os.path.join(PLANS_DIR, f"plan_{today}.json")
    
    if os.path.exists(today_file):
        print("\n" + "="*60)
        print(f" 🌅 BRIEFING FOR TODAY ({today})")
        print("="*60 + "\n")
        
        with open(today_file, "r") as f:
            data = json.load(f)
            print(json.dumps(data, indent=2))
        print("\n" + "="*60 + "\n")
    else:
        print(f"\nℹ️ No plan found for today ({today}).")

def create_plan_for_date(target_date, title_label):
    print(f"\n⚡ === Create Plan for {title_label} ({target_date}) ===")
    print("Enter your tasks/thoughts (type 'DONE' on a new line when finished):\n")
    
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
        print(f"\n⚡ MyTaskFlow is structuring your roadmap...\n")
        structured_plan = generate_ai_schedule(user_tasks, target_date)
        parsed = json.loads(structured_plan)
        
        plan_file = os.path.join(PLANS_DIR, f"plan_{target_date}.json")
        with open(plan_file, "w") as f:
            json.dump(parsed, f, indent=2)
            
        print(f"✅ Successfully saved plan to '{plan_file}'!")
        print("\nHere is your finalized plan:")
        print(json.dumps(parsed, indent=2))
    else:
        print("No tasks entered. Plan discarded.")

def start_live_monitor():
    today = date.today().isoformat()
    today_file = os.path.join(PLANS_DIR, f"plan_{today}.json")
    
    if not os.path.exists(today_file):
        print(f"\n❌ No plan found for today ({today}). Please create today's plan first using option [1]!")
        return

    with open(today_file, "r") as f:
        data = json.load(f)

    print(f"\n🔔 Live Task Monitor active for today ({today}).")
    print(f"Current local time: {datetime.now().strftime('%I:%M %p')}")
    print("Press Ctrl+C at any time to exit the monitor.\n")
    
    try:
        while True:
            current_time_str = datetime.now().strftime("%I:%M %p")
            
            for item in data.get("schedule", []):
                slot = item.get("time_slot", "")
                if current_time_str.lower() in slot.lower():
                    print("\n" + "!"*60)
                    print(f" 🚨 TASK ALERT! TIME FOR: {item.get('task')}")
                    print(f" 🕒 Slot: {slot} | Category: {item.get('category')}")
                    print(f" 💡 Tip: {item.get('quick_tip')}")
                    print("!"*60 + "\n")
                    
                    play_sound()
                    time.sleep(60)
                    
            time.sleep(30)
    except KeyboardInterrupt:
        print("\n🛑 Live Task Monitor stopped.")

if __name__ == "__main__":
    check_morning_reminder()
    
    print("What would you like to do?")
    print("  [1] Plan Today's Tasks (Instant / Test Mode)")
    print("  [2] Plan Tomorrow's Tasks (Evening Mode)")
    print("  [3] Start Live Task Monitor with Audio Alerts")
    print("  [4] Exit")
    
    choice = input("\nEnter choice (1, 2, 3, or 4): ").strip()
    if choice == '1':
        create_plan_for_date(date.today().isoformat(), "Today")
    elif choice == '2':
        create_plan_for_date((date.today() + timedelta(days=1)).isoformat(), "Tomorrow")
    elif choice == '3':
        start_live_monitor()
    else:
        print("Have a productive day!")
