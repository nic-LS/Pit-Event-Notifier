import os
import sys
import time
import requests
import threading
import tkinter as tk
from tkinter import ttk
from plyer import notification
from datetime import datetime, timezone

API_URL = "https://raw.githubusercontent.com/BrookeAFK/brookeafk-api/main/events.js"
FETCH_INTERVAL = 30 * 60
DISPLAY_INTERVAL = 1000
HEADERS = {"User-Agent": "Hypixel-Event-Checker/1.0"}
APP_ID = "Brother_Nic.HypixelPitEventNotifier"

MAJOR_EVENTS = ["Pizza", "Raffle", "Squads", "Spire", "Blockhead", "Robbery", "Team Deathmatch", "Rage Pit", "Beast"]
MINOR_EVENTS = ["2x Rewards", "KOTH", "KOTL", "Dragon Egg", "Care Package", "Auction", "Quick Maths", "Giant Cake", "All Bounty"]
ALL_EVENTS = MAJOR_EVENTS + MINOR_EVENTS

events = []
events_lock = threading.Lock()

def resource_path(relative_path):
    base_path = sys._MEIPASS if getattr(sys, "frozen", False) else os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

def get_icon_path():
    return resource_path(os.path.join("assets", "dirtblock.ico"))

def register_windows_app():
    if sys.platform != "win32":
        return

    try:
        import winreg
        import ctypes

        icon_path = get_icon_path()

        registry_path = r"Software\Classes\AppUserModelId\\" + APP_ID

        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, registry_path) as key:
            winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, "Hypixel Pit Event Notifier")
            winreg.SetValueEx(key, "IconUri", 0, winreg.REG_SZ, icon_path)
            winreg.SetValueEx(key, "IconBackgroundColor", 0, winreg.REG_SZ, "transparent")

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_ID)

    except Exception as e:
        print(f"Windows app registration failed: {e}")

def get_events():
    response = requests.get(API_URL, headers=HEADERS, timeout=10)
    response.raise_for_status()
    return response.json()

def fetch_loop(app):
    global events

    while True:
        try:
            new_events = get_events()

            with events_lock:
                events = new_events

            app.after(0, app.update_display)

        except requests.RequestException as e:
            print(f"API request failed: {e}")

        except (ValueError, TypeError, KeyError) as e:
            print(f"Invalid API response: {e}")

        time.sleep(FETCH_INTERVAL)

def format_countdown(seconds):
    seconds = max(0, int(seconds))
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    if hours:
        return f"{hours}h {minutes:02d}m {seconds:02d}s"

    if minutes:
        return f"{minutes}m {seconds:02d}s"

    return f"{seconds}s"

class EventApp(tk.Tk):
    def __init__(self):
        register_windows_app()
        super().__init__()

        icon_path = get_icon_path()

        try:
            if sys.platform == "win32":
                self.iconbitmap(default=icon_path)

        except tk.TclError as e:
            print(f"Could not load application icon: {e}")

        self.title("Hypixel Pit Event Notifier")
        self.geometry("900x700")
        self.minsize(700, 550)

        self.event_name_vars = {name: tk.BooleanVar(value=False) for name in ALL_EVENTS}
        self.name_checkbuttons = {}
        self.notifications_enabled = tk.BooleanVar(value=True)
        self.notification_minutes = tk.IntVar(value=5)
        self.starting_notification_minutes = tk.IntVar(value=1)
        self.notified_events = set()
        self.notification_lock = threading.Lock()
        self.create_widgets()
        self.update_event_names()
        self.update_display()
        threading.Thread(target=fetch_loop, args=(self,), daemon=True).start()

    def create_widgets(self):
        main = ttk.Frame(self, padding=10)
        main.pack(fill="both", expand=True)

        name_frame = ttk.LabelFrame(main, text="Events to Track", padding=10)
        name_frame.pack(fill="x", pady=(0, 10))

        buttons = ttk.Frame(name_frame)
        buttons.pack(fill="x", pady=(0, 10))

        ttk.Button(buttons, text="Select All", command=self.select_all_names).pack(side="left", padx=(0, 5))
        ttk.Button(buttons, text="Deselect All", command=self.deselect_all_names).pack(side="left")

        self.name_container = ttk.Frame(name_frame)
        self.name_container.pack(fill="x")
        self.name_container.bind("<Configure>", self.rebuild_event_grid)

        notification_frame = ttk.LabelFrame(main, text="Notification Settings", padding=10)
        notification_frame.pack(fill="x", pady=(0, 10))

        ttk.Checkbutton(notification_frame, text="Enable notifications", variable=self.notifications_enabled).grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 8))
        ttk.Label(notification_frame, text="Notify me:").grid(row=1, column=0, sticky="w")
        tk.Spinbox(notification_frame, from_=1, to=1440, width=5, textvariable=self.notification_minutes).grid(row=1, column=1, padx=5)
        ttk.Label(notification_frame, text="minutes before the event").grid(row=1, column=2, columnspan=2, sticky="w")
        ttk.Label(notification_frame, text="Event starting heads-up:").grid(row=2, column=0, sticky="w", pady=(8, 0))
        tk.Spinbox(notification_frame, from_=1, to=1440, width=5, textvariable=self.starting_notification_minutes).grid(row=2, column=1, padx=5, pady=(8, 0))
        ttk.Label(notification_frame, text="minute(s) before the event starts").grid(row=2, column=2, columnspan=2, sticky="w", pady=(8, 0))
        notification_frame.columnconfigure(3, weight=1)

        list_frame = ttk.LabelFrame(main, text="Upcoming Events", padding=10)
        list_frame.pack(fill="both", expand=True)

        columns = ("event", "type", "countdown")

        self.event_tree = ttk.Treeview(list_frame, columns=columns, show="headings")

        for column, heading in zip(columns, ("Event", "Type", "Starts In")):
            self.event_tree.heading(column, text=heading)

        self.event_tree.column("event", width=400)
        self.event_tree.column("type", width=150)
        self.event_tree.column("countdown", width=150, anchor="center")

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.event_tree.yview)
        self.event_tree.configure(yscrollcommand=scrollbar.set)

        self.event_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def get_grouped_events(self):
        return {"major": set(MAJOR_EVENTS), "minor": set(MINOR_EVENTS)}

    def update_event_names(self):
        for name in ALL_EVENTS:
            if name in self.name_checkbuttons:
                continue

            self.name_checkbuttons[name] = ttk.Checkbutton(self.name_container, text=name, variable=self.event_name_vars[name], command=self.update_display)

        self.rebuild_event_grid()

    def rebuild_event_grid(self, event=None):
        if not self.name_checkbuttons:
            return

        width = self.name_container.winfo_width()

        if width <= 1:
            return

        columns = max(1, width // 220)
        grouped = self.get_grouped_events()

        for widget in self.name_container.winfo_children():
            widget.grid_forget()

        for column in range(columns):
            self.name_container.columnconfigure(column, weight=1)

        row = 0

        for group_name, heading in (("major", "Major Events"), ("minor", "Minor Events")):
            names = sorted(grouped[group_name])

            if not names:
                continue

            ttk.Label(self.name_container, text=heading, font=("TkDefaultFont", 10, "bold")).grid(row=row, column=0, columnspan=columns, sticky="w", pady=(0, 5))

            row += 1

            for index, name in enumerate(names):
                checkbox = self.name_checkbuttons.get(name)

                if checkbox is None:
                    continue

                checkbox.grid(row=row + index // columns, column=index % columns, sticky="w", padx=(0, 20), pady=3)

            row += (len(names) + columns - 1) // columns
            row += 1

    def select_all_names(self):
        for var in self.event_name_vars.values():
            var.set(True)

        self.update_display()

    def deselect_all_names(self):
        for var in self.event_name_vars.values():
            var.set(False)

        self.update_display()

    def get_notification_minutes(self):
        try:
            return max(1, int(self.notification_minutes.get()))

        except (ValueError, tk.TclError):
            return None

    def get_starting_notification_minutes(self):
        try:
            return max(1, int(self.starting_notification_minutes.get()))

        except (ValueError, tk.TclError):
            return None

    def send_notification(self, event_name, event_type, remaining, notification_kind):
        action = "is starting" if notification_kind == "starting" else "starts"
        countdown = format_countdown(remaining)

        try:
            notification.notify(
                title="Hypixel Pit Event",
                message=f"{event_name} ({event_type}) {action} in {countdown}!",
                app_name="Hypixel Pit Event Notifier",
                timeout=10
            )

        except Exception as e:
            print(f"Notification failed: {e}")

    def trigger_notification(self, event_id, event_name, event_type, remaining, notification_kind):
        with self.notification_lock:
            if event_id in self.notified_events:
                return

            self.notified_events.add(event_id)

        self.send_notification(event_name, event_type, remaining, notification_kind)

    def check_notifications(self, current_events, now):
        if not self.notifications_enabled.get():
            return

        notification_minutes = self.get_notification_minutes()
        starting_minutes = self.get_starting_notification_minutes()

        if notification_minutes is None or starting_minutes is None:
            return

        for event in current_events:
            try:
                name = event["event"]
                event_type = event["type"]
                timestamp = event["timestamp"]

            except KeyError:
                continue

            if name not in self.event_name_vars:
                continue

            if not self.event_name_vars[name].get():
                continue

            remaining = timestamp / 1000 - now

            if remaining <= 0:
                continue

            if remaining <= notification_minutes * 60:
                self.trigger_notification((name, timestamp, "normal"), name, event_type, remaining, "normal")

            if remaining <= starting_minutes * 60:
                self.trigger_notification((name, timestamp, "starting"), name, event_type, remaining, "starting")

    def update_display(self):
        now = datetime.now(timezone.utc).timestamp()
        now_ms = now * 1000

        with events_lock:
            current_events = events.copy()

        self.check_notifications(current_events, now)

        upcoming = []

        for event in current_events:
            try:
                name = event["event"]
                event_type = event["type"]
                timestamp = event["timestamp"]

            except KeyError:
                continue

            if name not in self.event_name_vars:
                continue

            if not self.event_name_vars[name].get():
                continue

            remaining = (timestamp - now_ms) / 1000

            if remaining > 0:
                upcoming.append((name, event_type, remaining))

        upcoming.sort(key=lambda event: event[2])

        for item in self.event_tree.get_children():
            self.event_tree.delete(item)

        for name, event_type, remaining in upcoming:
            self.event_tree.insert("", "end", values=(name, event_type, format_countdown(remaining)))

        self.after(DISPLAY_INTERVAL, self.update_display)

def main():
    EventApp().mainloop()

if __name__ == "__main__":
    main()
