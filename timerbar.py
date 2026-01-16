import argparse
import tkinter as tk
from screeninfo import get_monitors
import requests 
import time
import threading
import queue

class SteadyTopTimer:
    def __init__(self, duration_seconds=600, server_url=None, auth_token=None, ca_cert=None, start_fade=15, end_fade=45):
        self.server_url = server_url
        self.auth_token = auth_token
        self.ca_cert = ca_cert
        
        self.start_fade = start_fade
        self.end_fade = end_fade
        
        self.monitors = get_monitors()
        self.windows = []
        self.bars = []
        self.labels = []
        
        self.total_seconds = float(duration_seconds)
        self.remaining_seconds = self.total_seconds
        self.end_time = 0 
        self.is_paused = True
        self.bar_height = 25 
        
        self.color_start_rgb = (0, 136, 58)   # Green
        self.color_end_rgb = (178, 34, 34)    # Red
        
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

            prog = canvas.create_rectangle(0, 0, 0, self.bar_height, fill="#00883A", outline="")
            
            # MOVED TO MIDDLE: 
            # Changed x-coordinate to 0 (placeholder) and anchor to "center"
            txt = canvas.create_text(0, self.bar_height/2, text="", fill="white", anchor="center", font=("Arial", 10, "bold"))

            self.windows.append(win)
            self.bars.append((canvas, prog))
            self.labels.append(txt)

        self.update_ui()
        self.tick()
        if server_url:
            self.start_poll_thread()
            self.process_poll_commands()
        self.root.mainloop()

    def interpolate_color(self, factor):
        r = int(self.color_start_rgb[0] + (self.color_end_rgb[0] - self.color_start_rgb[0]) * factor)
        g = int(self.color_start_rgb[1] + (self.color_end_rgb[1] - self.color_start_rgb[1]) * factor)
        b = int(self.color_start_rgb[2] + (self.color_end_rgb[2] - self.color_start_rgb[2]) * factor)
        return f'#{r:02x}{g:02x}{b:02x}'

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
                    headers = {"X-Auth-Token": self.auth_token} if self.auth_token else {}
                    response = requests.get(f"{self.server_url}/status", timeout=0.5, headers=headers, verify=self.ca_cert or True)
                    if response.status_code == 200:
                        cmd = response.json().get("last_command")
                        if cmd in ("toggle", "reset"): self.cmd_queue.put(cmd)
                except Exception: pass
                self.poll_stop.wait(0.5)
        threading.Thread(target=_poll_loop, daemon=True).start()

    def process_poll_commands(self):
        try:
            while True:
                cmd = self.cmd_queue.get_nowait()
                if cmd == "toggle": self.toggle_pause()
                elif cmd == "reset": self.reset()
        except queue.Empty: pass
        self.root.after(100, self.process_poll_commands)

    def toggle_pause(self):
        self.is_paused = not self.is_paused
        if not self.is_paused:
            self.end_time = time.time() + self.remaining_seconds
        self.btn_start.config(text="⏸" if not self.is_paused else "▶")

    def reset(self):
        self.remaining_seconds = self.total_seconds
        self.is_paused = True
        self.btn_start.config(text="▶")
        self.update_ui()

    def update_ui(self):
        overtime_seconds = -self.remaining_seconds
        is_overtime = self.remaining_seconds < 0
        
        # Color Logic
        if not is_overtime:
            current_color = f'#{self.color_start_rgb[0]:02x}{self.color_start_rgb[1]:02x}{self.color_start_rgb[2]:02x}'
            percent = max(0, min(1, (self.total_seconds - self.remaining_seconds) / self.total_seconds))
        else:
            percent = 1.0 
            if overtime_seconds <= self.start_fade:
                current_color = self.interpolate_color(0.0)
            elif overtime_seconds >= self.end_fade:
                current_color = self.interpolate_color(1.0)
            else:
                factor = (overtime_seconds - self.start_fade) / (self.end_fade - self.start_fade)
                current_color = self.interpolate_color(factor)

        # Format Strings
        abs_seconds = abs(int(self.remaining_seconds))
        mins, secs = divmod(abs_seconds, 60)
        time_str = f"{'-' if is_overtime else ''}{mins:02d}:{secs:02d}"

        # Update each monitor
        for i, (canvas, prog) in enumerate(self.bars):
            canvas_width = canvas.winfo_width()
            if canvas_width <= 1: canvas_width = self.monitors[i].width
            
            # Update bar width
            new_width = percent * canvas_width
            canvas.coords(prog, 0, 0, new_width, self.bar_height)
            canvas.itemconfig(prog, fill=current_color)
            
            # UPDATE TEXT POSITION: Center it based on current canvas width
            canvas.coords(self.labels[i], canvas_width / 2, self.bar_height / 2)
            canvas.itemconfigure(self.labels[i], text=time_str)

    def tick(self):
        if not self.is_paused:
            self.remaining_seconds = self.end_time - time.time()
            self.update_ui()
        self.root.after(50, self.tick)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--duration-seconds", type=int, default=600)
    parser.add_argument("--start-fade", type=int, default=15)
    parser.add_argument("--end-fade", type=int, default=45)
    parser.add_argument("--server-url", default=None)
    parser.add_argument("--auth-token", default=None)
    parser.add_argument("--ca-cert", default=None)
    
    args = parser.parse_args()
    SteadyTopTimer(
        duration_seconds=args.duration_seconds,
        start_fade=args.start_fade,
        end_fade=args.end_fade,
        server_url=args.server_url,
        auth_token=args.auth_token,
        ca_cert=args.ca_cert,
    )