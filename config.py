import json
import os
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
REMINDERS_FILE = os.path.join(DATA_DIR, "reminders.json")
SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")


def _ensure_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def load_reminders():
    _ensure_dir()
    if not os.path.exists(REMINDERS_FILE):
        return []
    with open(REMINDERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_reminders(reminders):
    _ensure_dir()
    with open(REMINDERS_FILE, "w", encoding="utf-8") as f:
        json.dump(reminders, f, ensure_ascii=False, indent=2)


def add_reminder(time_str, content):
    reminders = load_reminders()
    reminders.append({
        "time": time_str,
        "content": content,
        "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "fired": False
    })
    save_reminders(reminders)
    return reminders


def remove_reminder(index):
    reminders = load_reminders()
    if 0 <= index < len(reminders):
        reminders.pop(index)
        save_reminders(reminders)
    return reminders


def get_pending_reminders():
    now = datetime.now()
    pending = []
    reminders = load_reminders()
    for i, r in enumerate(reminders):
        if r.get("fired"):
            continue
        try:
            reminder_time = datetime.strptime(r["time"], "%Y-%m-%d %H:%M")
            if reminder_time <= now:
                pending.append((i, r))
        except ValueError:
            continue
    return pending


def mark_reminder_fired(index):
    reminders = load_reminders()
    if 0 <= index < len(reminders):
        reminders[index]["fired"] = True
        save_reminders(reminders)


def load_settings():
    _ensure_dir()
    defaults = {
        "pet_x": 800,
        "pet_y": 400,
        "pet_size": 150
    }
    if not os.path.exists(SETTINGS_FILE):
        return defaults
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            settings = json.load(f)
            defaults.update(settings)
            return defaults
    except (json.JSONDecodeError, KeyError):
        return defaults


def save_settings(settings):
    _ensure_dir()
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)
