import argparse
import tkinter as tk
from screeninfo import get_monitors
import requests 
import time
import threading
import queue

class SteadyTopTimer:
    def __init__(self, duration_minutes=10, server_url=None, auth_token=None):
        self.server_url = server_url
        self.auth_token = auth_token
        
        self.monitors = get_monitors()
        self.windows = []
        self.bars = []
        self.labels = []
        
        self.total_seconds = duration_minutes * 60
        self.remaining_seconds = self.total_seconds
        self.end_time = 0 # Stores the target system time
        self.is_paused = True
        self.bar_height = 25 
        self.bar_color = "#00883A"
        self.cmd_queue = queue.Queue()
        self.poll_stop = threading.Event()

        for i, m in enumerate(self.monitors):
            is_main = (i == 0)
            win = tk.Tk() if is_main else tk.Toplevel()
            if is_main: self.root = win
            
            win.overrideredirect(True)
            win.attributes("-topmost", True)
            win.geometry(f"{m.width}x{self.bar_height}+{m.x}+{m.y}")

            if is_main: self.setup_main_controls(win) 
            
            canvas = tk.Canvas(win, bg="#111", highlightthickness=0, height=self.bar_height)
            canvas.pack(side="left", fill="both", expand=True)

            prog = canvas.create_rectangle(0, 0, 0, self.bar_height, fill=self.bar_color, outline="")
            txt = canvas.create_text(15, self.bar_height/2, text="", fill="white", anchor="w", font=("Arial", 9, "bold"))

            self.windows.append(win)
            self.bars.append((canvas, prog))
            self.labels.append(txt)

        self.update_ui()
        self.tick()
        if server_url:
            self.start_poll_thread()
            self.process_poll_commands()
        self.root.mainloop()

    def setup_main_controls(self, win):
        ctrl_frame = tk.Frame(win, bg="#111")
        ctrl_frame.pack(side="left", fill="y")
        
        self.btn_start = tk.Button(ctrl_frame, text="▶", command=self.toggle_pause, bg="#444", fg="white", bd=0, width=4)
        self.btn_start.pack(side="left", padx=2, fill="y")
        
        tk.Button(ctrl_frame, text="↺", command=self.reset, bg="#444", fg="white", bd=0, width=4).pack(side="left", padx=2, fill="y")
        tk.Button(ctrl_frame, text="✕", command=self.root.destroy, bg="#b22", fg="white", bd=0, width=4).pack(side="left", padx=2, fill="y")

    def start_poll_thread(self):
        def _poll_loop():
            while not self.poll_stop.is_set():
                try:
                    headers = {}
                    if self.auth_token:
                        headers["X-Auth-Token"] = self.auth_token
                    response = requests.get(
                        f"{self.server_url}/status",
                        timeout=0.5,
                        headers=headers,
                    )
                    if response.status_code == 200:
                        cmd = response.json().get("last_command")
                        if cmd in ("toggle", "reset"):
                            self.cmd_queue.put(cmd)
                except Exception:
                    pass
                self.poll_stop.wait(1.0)

        t = threading.Thread(target=_poll_loop, daemon=True)
        t.start()

    def process_poll_commands(self):
        try:
            while True:
                cmd = self.cmd_queue.get_nowait()
                if cmd == "toggle":
                    self.toggle_pause()
                elif cmd == "reset":
                    self.reset()
        except queue.Empty:
            pass
        self.root.after(100, self.process_poll_commands)

    def toggle_pause(self):
        self.is_paused = not self.is_paused
        if not self.is_paused:
            # Recalculate the 'finish line' relative to right now
            self.end_time = time.time() + self.remaining_seconds
        self.btn_start.config(text="⏸" if not self.is_paused else "▶")

    def reset(self):
        self.remaining_seconds = self.total_seconds
        self.is_paused = True
        self.btn_start.config(text="▶")
        self.update_ui()

    def update_ui(self):
        elapsed = self.total_seconds - self.remaining_seconds
        percent = max(0, min(1, elapsed / self.total_seconds))
        
        mins, secs = divmod(int(self.remaining_seconds), 60)
        time_str = f"{mins:02d}:{secs:02d}"

        for i, (canvas, prog) in enumerate(self.bars):
            canvas_width = canvas.winfo_width()
            if canvas_width <= 1: canvas_width = self.monitors[i].width
            
            new_width = percent * canvas_width
            canvas.coords(prog, 0, 0, new_width, self.bar_height)
            canvas.itemconfig(prog, fill=self.bar_color)
            canvas.itemconfigure(self.labels[i], text=time_str)

    def tick(self):
        if not self.is_paused and self.remaining_seconds > 0:
            # Logic: Remaining = Target Finish Time - Current Time
            self.remaining_seconds = max(0, self.end_time - time.time())
            self.update_ui()
            
            if self.remaining_seconds == 0:
                self.is_paused = True
                self.btn_start.config(text="▶")

        # Running tick more frequently (e.g. 200ms) makes the bar 
        # look smoother without losing accuracy.
        self.root.after(50, self.tick)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--duration-minutes", type=int, default=10)
    parser.add_argument("--server-url", default=None)
    parser.add_argument("--auth-token", default=None)
    args = parser.parse_args()

    SteadyTopTimer(
        duration_minutes=args.duration_minutes,
        server_url=args.server_url,
        auth_token=args.auth_token,
    )
