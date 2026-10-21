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
        subprocess.run(["afplay", "/System/Library/Sounds/Glass.aiff"], check=False)
        subprocess.run(["say", f"Task alert: {task_name}"], check=False)
    except Exception:
        print("\a\a\a")

def parse_time(time_str):
    try:
        return datetime.strptime(time_str.strip(), "%I:%M %p").time()
    except ValueError:
        return None

def generate_ai_schedule(raw_input, date_label):
    current_time_hint = datetime.now().strftime("%I:%M %p")
    prompt = f"""
    You are MyTaskFlow AI, an elite productivity assistant.
    Take the following raw, unorganized tasks/thoughts and organize them into an optimal schedule for {date_label}.
    IMPORTANT: The current time right now is {current_time_hint}. Make sure at least one task's time slot covers the current time ({current_time_hint}) if planning for today.
    
    Raw Input:
    {raw_input}
    
    Output structured JSON format:
    {{
      "schedule_date": "{date_label}",
      "schedule": [
        {{
          "id": 1,
          "time_slot": "09:00 AM - 10:00 AM",
          "task": "Task name",
          "priority": "High/Medium/Low",
          "category": "Work/Personal/Health/Admin",
          "quick_tip": "Actionable tip to complete efficiently",
          "completed": false
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
            
        for item in data.get("schedule", []):
            status = "✅" if item.get("completed") else "⏳"
            print(f"{status} [{item.get('id', '-')}] {item.get('time_slot')}: {item.get('task')}")
            
        print("\n💡 Quote:", data.get("productivity_quote", ""))
        print("\n" + "="*60 + "\n")
    else:
        print(f"\nℹ️ No plan found for today ({today}).")

def mark_task_complete():
    today = date.today().isoformat()
    today_file = os.path.join(PLANS_DIR, f"plan_{today}.json")
    
    if not os.path.exists(today_file):
        print("❌ No plan found for today to update.")
        return

    with open(today_file, "r") as f:
        data = json.load(f)

    schedule = data.get("schedule", [])
    if not schedule:
        print("No tasks found.")
        return

    print("\nCurrent Tasks:")
    for idx, item in enumerate(schedule, start=1):
        status = "✅ Done" if item.get("completed") else "⏳ Pending"
        print(f"  [{idx}] {item.get('task')} ({status})")

    choice = input("\nEnter task number to mark complete: ").strip()
    if choice.isdigit():
        task_idx = int(choice) - 1
        if 0 <= task_idx < len(schedule):
            schedule[task_idx]["completed"] = True
            data["schedule"] = schedule
            with open(today_file, "w") as f:
                json.dump(data, f, indent=2)
            print(f"🎉 Marked '{schedule[task_idx]['task']}' as complete!")
        else:
            print("Invalid task number.")

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
    else:
        print("No tasks entered. Plan discarded.")

def start_live_monitor():
    today = date.today().isoformat()
    today_file = os.path.join(PLANS_DIR, f"plan_{today}.json")
    
    if not os.path.exists(today_file):
        print(f"\n❌ No plan found for today ({today}). Please create today's plan first!")
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
            
            # Reload to capture any completed task updates
            with open(today_file, "r") as f:
                data = json.load(f)

            for item in data.get("schedule", []):
                if item.get("completed"):
                    continue

                task_name = item.get("task", "Task")
                slot = item.get("time_slot", "")
                
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

def main():
    check_morning_reminder()
    
    print("What would you like to do?")
    print("  [1] Plan Today's Tasks")
    print("  [2] Plan Tomorrow's Tasks (Evening Mode)")
    print("  [3] Start Live Task Monitor with Audio Alerts")
    print("  [4] Mark Task as Completed")
    print("  [5] Exit")
    
    choice = input("\nEnter choice (1-5): ").strip()
    if choice == '1':
        create_plan_for_date(date.today().isoformat(), "Today")
    elif choice == '2':
        create_plan_for_date((date.today() + timedelta(days=1)).isoformat(), "Tomorrow")
    elif choice == '3':
        start_live_monitor()
    elif choice == '4':
        mark_task_complete()
    else:
        print("Have a productive day!")

if __name__ == "__main__":
    main()
