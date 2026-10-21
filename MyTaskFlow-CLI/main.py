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

def play_sound(task_name="Task"):
    """Triggers an audio alert using Mac native text-to-speech sound system."""
    try:
        # 1. Play native macOS Glass chime
        subprocess.run(["afplay", "/System/Library/Sounds/Glass.aiff"], check=False)
        # 2. Spoken alert banner
        subprocess.run(["say", f"Task alert: {task_name}"], check=False)
    except Exception:
        print("\a\a\a") # Fallback terminal beep

def parse_time(time_str):
    """Converts a time string like '10:36 PM' to a datetime object for accurate time comparisons."""
    try:
        return datetime.strptime(time_str.strip(), "%I:%M %p").time()
    except ValueError:
        return None

def generate_ai_schedule(raw_input, date_label):
    current_time_hint = datetime.now().strftime("%I:%M %p")
    prompt = f"""
    You are MyTaskFlow AI, an elite productivity assistant.
    Take the following raw, unorganized tasks/thoughts and organize them into an optimal schedule for {date_label}.
    IMPORTANT: The current time right now is {current_time_hint}. Make sure at least one task's time slot covers the current time ({current_time_hint}) so the user can test the live monitor alert immediately.
    
    Raw Input:
    {raw_input}
    
    Output structured JSON format:
    {{
      "schedule_date": "{date_label}",
      "schedule": [
        {{
          "time_slot": "10:30 PM - 11:00 PM",
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
    
    triggered_tasks = set()

    try:
        while True:
            now = datetime.now()
            current_time = now.time()
            current_str = now.strftime("%I:%M %p")
            
            for item in data.get("schedule", []):
                task_name = item.get("task", "Task")
                slot = item.get("time_slot", "")
                
                # Check if current time string is anywhere in slot OR perform range check
                parts = slot.split("-")
                in_range = False
                
                if len(parts) == 2:
                    start_t = parse_time(parts[0])
                    end_t = parse_time(parts[1])
                    if start_t and end_t and start_t <= current_time <= end_t:
                        in_range = True
                elif current_str.lower() in slot.lower():
                    in_range = True

                if in_range and task_name not in triggered_tasks:
                    print("\n" + "!"*60)
                    print(f" 🚨 TASK ALERT! TIME FOR: {task_name}")
                    print(f" 🕒 Slot: {slot} | Category: {item.get('category')}")
                    print(f" 💡 Tip: {item.get('quick_tip')}")
                    print("!"*60 + "\n")
                    
                    play_sound(task_name)
                    triggered_tasks.add(task_name)
                    
            time.sleep(10)
    except KeyboardInterrupt:
        print("\n🛑 Live Task Monitor stopped.")

def test_sound_now():
    print("\n🔊 Testing audio ringtone and voice alert...")
    play_sound("Test Ringtone Task")
    print("✅ Sound test completed!\n")

if __name__ == "__main__":
    check_morning_reminder()
    
    print("What would you like to do?")
    print("  [1] Plan Today's Tasks (Instant / Test Mode)")
    print("  [2] Plan Tomorrow's Tasks (Evening Mode)")
    print("  [3] Start Live Task Monitor with Audio Alerts")
    print("  [4] Test Audio Alert Ringtone Immediately")
    print("  [5] Exit")
    
    choice = input("\nEnter choice (1, 2, 3, 4, or 5): ").strip()
    if choice == '1':
        create_plan_for_date(date.today().isoformat(), "Today")
    elif choice == '2':
        create_plan_for_date((date.today() + timedelta(days=1)).isoformat(), "Tomorrow")
    elif choice == '3':
        start_live_monitor()
    elif choice == '4':
        test_sound_now()
    else:
        print("Have a productive day!")
