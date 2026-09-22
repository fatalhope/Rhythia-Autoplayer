import tkinter as tk
from tkinter import filedialog, simpledialog
import threading
import time
import keyboard
import pydirectinput


# ============================================================
#  CONFIG
# ============================================================
class Config:
    MAP_PATH = ""
    START_KEY = "right shift"
    START_NOW_KEY = "right ctrl"
    STOP_KEY = "left shift"
    TOGGLE_UI_KEY = "insert"

    IS_RUNNING = False
    NOTES = []

    TIMING_OFFSET_MS = 0
    START_OFFSET_MS = 0
    SPEED = 1.0
    PITCH_LOCK = True
    CENTER_X = 958
    CENTER_Y = 563
    BASE_OFFSET = 295

    SONG_DURATION_MS = 0


# ============================================================
#  SSPM LOADER
# ============================================================
def load_sspm(path):
    try:
        import pysspm_rhythia
    except ImportError:
        print("[ERROR] Missing pysspm_rhythia")
        return [], 0

    try:
        data = pysspm_rhythia.read_sspm(path)
    except Exception as e:
        print(f"[ERROR] {e}")
        return [], 0

    if not hasattr(data, "notes"):
        return [], 0

    notes = []
    for n in data.notes:
        if isinstance(n, (tuple, list)) and len(n) >= 3:
            notes.append({"x": int(n[0]), "y": int(n[1]), "ms": int(n[2])})
        elif isinstance(n, dict):
            notes.append({
                "x": int(n.get("x", 0)),
                "y": int(n.get("y", 0)),
                "ms": int(n.get("ms") or n.get("time") or n.get("t", 0))
            })
        elif hasattr(n, "x"):
            notes.append({
                "x": int(getattr(n, "x", 0)),
                "y": int(getattr(n, "y", 0)),
                "ms": int(getattr(n, "ms", 0))
            })

    notes.sort(key=lambda n: n["ms"])
    duration = notes[-1]["ms"] if notes else 0

    if hasattr(data, "song_length"):
        try:
            duration = int(data.song_length)
        except:
            pass
    elif hasattr(data, "duration"):
        try:
            duration = int(data.duration)
        except:
            pass

    print(f"[INFO] Loaded {len(notes)} notes, duration ~{duration} ms")
    return notes, duration


# ============================================================
#  AUTOPLAYER
# ============================================================
class AutoPlayer:
    def __init__(self):
        self.running = True
        self.stop_flag = threading.Event()
        pydirectinput.PAUSE = 0.001
        pydirectinput.FAILSAFE = False
        self.song_start_ms = 0

    def start(self):
        threading.Thread(target=self._key_listener, daemon=True).start()

    def _key_listener(self):
        while self.running:
            if keyboard.is_pressed(Config.START_KEY):
                if not Config.IS_RUNNING and Config.NOTES:
                    Config.IS_RUNNING = True
                    self.stop_flag.clear()
                    self.song_start_ms = time.time() * 1000
                    threading.Thread(target=self._play, daemon=True).start()
                time.sleep(0.3)

            if keyboard.is_pressed(Config.START_NOW_KEY):
                if not Config.IS_RUNNING and Config.NOTES:
                    Config.IS_RUNNING = True
                    self.stop_flag.clear()
                    self.song_start_ms = time.time() * 1000
                    threading.Thread(target=self._play, daemon=True).start()
                time.sleep(0.3)

            if keyboard.is_pressed(Config.STOP_KEY):
                if Config.IS_RUNNING:
                    Config.IS_RUNNING = False
                    self.stop_flag.set()
                time.sleep(0.3)

            time.sleep(0.01)

    def _play(self):
        print(f"[PLAY] Started speed={Config.SPEED}x")
        start_time = time.time() * 1000 - Config.START_OFFSET_MS

        for note in Config.NOTES:
            if not Config.IS_RUNNING:
                print("[PLAY] Stopped")
                return

            scaled_ms = note["ms"] / Config.SPEED
            target_ms = scaled_ms + Config.TIMING_OFFSET_MS

            if target_ms < Config.START_OFFSET_MS:
                continue

            current_ms = time.time() * 1000 - start_time
            wait = (target_ms - current_ms) / 1000.0

            if wait > 0:
                if self.stop_flag.wait(wait):
                    return

            pos_x = Config.CENTER_X + (note["x"] - 1) * Config.BASE_OFFSET
            pos_y = Config.CENTER_Y + (note["y"] - 1) * Config.BASE_OFFSET

            try:
                pydirectinput.moveTo(int(pos_x), int(pos_y))
                pydirectinput.click()
            except:
                pass

        print("[PLAY] Finished")
        Config.IS_RUNNING = False


# ============================================================
#  UI
# ============================================================
class OverlayApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Rhythia Auto")
        self.geometry("460x800+50+50")
        self.configure(bg="#0a0a0a")
        self.attributes("-topmost", True)
        self.attributes("-alpha", 0.0)
        self.resizable(False, False)

        self.visible = False
        self.withdraw()

        self.BG_TOP = "#0a0a0a"
        self.BG_CARD = "#1a1a1a"
        self.BG_CARD_HI = "#222222"
        self.BG_INPUT = "#101010"
        self.FG_MUTED = "#7a7a7a"
        self.FG_TEXT = "#e8e8e8"
        self.ACCENT = "#ffcc00"
        self.ACCENT_HI = "#ffd633"
        self.GREEN = "#00e676"
        self.BLUE = "#5d5dff"
        self.RED = "#ff5252"

        self.f_title = ("Segoe UI", 16, "bold")
        self.f_sub = ("Segoe UI", 9)
        self.f_label = ("Segoe UI", 10)
        self.f_value = ("Segoe UI", 11, "bold")
        self.f_btn = ("Segoe UI", 10, "bold")
        self.f_btn_small = ("Segoe UI", 12, "bold")
        self.f_big = ("Segoe UI", 16, "bold")

        self.speed_options = ["0.75x", "0.8x", "0.87x", "1x",
                              "1.15x", "1.25x", "1.35x", "1.45x", "Custom"]

        self.player = AutoPlayer()
        self.player.start()

        self.build_ui()
        self.bind_hotkeys()
        self.animate_status()
        self.update_status()

    def draw_gradient(self, canvas, w, h):
        for i in range(h):
            v = int(10 + (22 - 10) * (i / h))
            color = f"#{v:02x}{v:02x}{v:02x}"
            canvas.create_line(0, i, w, i, fill=color)

    def build_ui(self):
        W, H = 460, 800

        self.canvas = tk.Canvas(self, width=W, height=H, highlightthickness=0, bd=0)
        self.canvas.pack(fill="both", expand=True)
        self.draw_gradient(self.canvas, W, H)

        self.container = tk.Frame(self.canvas, bg=self.BG_TOP)
        self.canvas.create_window(0, 0, anchor="nw", window=self.container, width=W, height=H)

        # HEADER
        header = tk.Frame(self.container, bg=self.BG_TOP)
        header.pack(fill="x", padx=24, pady=(22, 4))

        tk.Label(header, text="Rhythia Auto", fg=self.FG_TEXT, bg=self.BG_TOP,
                 font=self.f_title, anchor="w").pack(anchor="w")
        tk.Label(header, text="Press Insert to toggle panel",
                 fg=self.FG_MUTED, bg=self.BG_TOP, font=self.f_sub,
                 anchor="w").pack(anchor="w", pady=(2, 0))

        # CHOOSE FILE
        self.btn_load = tk.Button(
            self.container, text="Choose .sspm file",
            bg=self.ACCENT, fg="#000000",
            font=self.f_btn, relief="flat", bd=0, pady=12,
            activebackground=self.ACCENT_HI, activeforeground="#000000",
            cursor="hand2", command=self.pick_file
        )
        self.btn_load.pack(fill="x", padx=24, pady=(18, 8))
        self.add_hover(self.btn_load, self.ACCENT, self.ACCENT_HI)

        # STATUS CARD
        status_card = self.make_card()
        inner = tk.Frame(status_card, bg=self.BG_CARD)
        inner.pack(fill="x", padx=16, pady=14)

        tk.Label(inner, text="STATUS", fg=self.FG_MUTED, bg=self.BG_CARD,
                 font=self.f_sub, anchor="w").grid(row=0, column=0, sticky="w")

        st_right = tk.Frame(inner, bg=self.BG_CARD)
        st_right.grid(row=0, column=1, sticky="e")
        self.dot = tk.Canvas(st_right, width=12, height=12, bg=self.BG_CARD,
                             highlightthickness=0, bd=0)
        self.dot.pack(side="left", padx=(0, 8))
        self.dot_id = self.dot.create_oval(2, 2, 10, 10, fill=self.BLUE, outline="")
        self.lbl_mode = tk.Label(st_right, text="IDLE", fg=self.BLUE, bg=self.BG_CARD,
                                 font=self.f_value, anchor="e")
        self.lbl_mode.pack(side="left")

        tk.Label(inner, text="NOTES LOADED", fg=self.FG_MUTED, bg=self.BG_CARD,
                 font=self.f_sub, anchor="w").grid(row=1, column=0, sticky="w", pady=(8, 0))
        self.lbl_notes = tk.Label(inner, text="0", fg=self.BLUE, bg=self.BG_CARD,
                                  font=self.f_value, anchor="e")
        self.lbl_notes.grid(row=1, column=1, sticky="e", pady=(8, 0))

        tk.Label(inner, text="SPEED", fg=self.FG_MUTED, bg=self.BG_CARD,
                 font=self.f_sub, anchor="w").grid(row=2, column=0, sticky="w", pady=(8, 0))
        self.lbl_speed = tk.Label(inner, text="1.00x", fg=self.ACCENT, bg=self.BG_CARD,
                                  font=self.f_value, anchor="e")
        self.lbl_speed.grid(row=2, column=1, sticky="e", pady=(8, 0))

        inner.columnconfigure(1, weight=1)

        # PROGRESS CARD
        progress_card = self.make_card()
        inner_pg = tk.Frame(progress_card, bg=self.BG_CARD)
        inner_pg.pack(fill="x", padx=16, pady=12)

        top = tk.Frame(inner_pg, bg=self.BG_CARD)
        top.pack(fill="x")
        tk.Label(top, text="PROGRESS", fg=self.FG_MUTED, bg=self.BG_CARD,
                 font=self.f_sub).pack(side="left")
        self.lbl_time = tk.Label(top, text="00:00 / 00:00", fg=self.FG_TEXT,
                                 bg=self.BG_CARD, font=self.f_label)
        self.lbl_time.pack(side="right")

        self.progress_canvas = tk.Canvas(inner_pg, height=6, bg=self.BG_INPUT,
                                         highlightthickness=0, bd=0)
        self.progress_canvas.pack(fill="x", pady=(8, 0))
        self.progress_bar = self.progress_canvas.create_rectangle(
            0, 0, 0, 6, fill=self.ACCENT, outline="")

        # TIMING CARD
        timing_card = self.make_card()
        inner_t = tk.Frame(timing_card, bg=self.BG_CARD)
        inner_t.pack(fill="x", padx=16, pady=14)

        tk.Label(inner_t, text="TIMING OFFSET", fg=self.FG_MUTED, bg=self.BG_CARD,
                 font=self.f_sub, anchor="w").pack(anchor="w")

        row = tk.Frame(inner_t, bg=self.BG_CARD)
        row.pack(fill="x", pady=(8, 0))
        self.lbl_timing = tk.Label(row, text="0 ms", fg=self.ACCENT, bg=self.BG_CARD,
                                   font=self.f_big)
        self.lbl_timing.pack(side="left")

        bf = tk.Frame(row, bg=self.BG_CARD)
        bf.pack(side="right")
        self.make_small_btn(bf, "-", self.RED, lambda: self.adjust_timing(-5))
        self.make_small_btn(bf, "+", self.GREEN, lambda: self.adjust_timing(5))

        # START FROM CARD
        start_card = self.make_card()
        inner_s = tk.Frame(start_card, bg=self.BG_CARD)
        inner_s.pack(fill="x", padx=16, pady=14)

        tk.Label(inner_s, text="START FROM", fg=self.FG_MUTED, bg=self.BG_CARD,
                 font=self.f_sub, anchor="w").pack(anchor="w")

        row2 = tk.Frame(inner_s, bg=self.BG_CARD)
        row2.pack(fill="x", pady=(8, 0))
        self.lbl_start = tk.Label(row2, text="0 ms", fg=self.ACCENT, bg=self.BG_CARD,
                                  font=self.f_big)
        self.lbl_start.pack(side="left")

        bf2 = tk.Frame(row2, bg=self.BG_CARD)
        bf2.pack(side="right")
        self.make_small_btn(bf2, "-1s", self.RED, lambda: self.adjust_start(-1000), width=4)
        self.make_small_btn(bf2, "+1s", self.GREEN, lambda: self.adjust_start(1000), width=4)
        self.make_small_btn(bf2, "R", self.FG_TEXT, self.reset_start, width=3)

        # SPEED CARD
        speed_card = self.make_card(pad_bottom=14)
        head = tk.Frame(speed_card, bg=self.BG_CARD)
        head.pack(fill="x", padx=16, pady=(14, 6))

        tk.Label(head, text="PLAYBACK SPEED", fg=self.FG_MUTED, bg=self.BG_CARD,
                 font=self.f_sub).pack(side="left")

        self.pitch_var = tk.BooleanVar(value=Config.PITCH_LOCK)
        self.chk_pitch = tk.Checkbutton(head, text="Pitch Lock", variable=self.pitch_var,
                                        bg=self.BG_CARD, fg=self.FG_TEXT,
                                        selectcolor=self.BG_INPUT,
                                        activebackground=self.BG_CARD,
                                        activeforeground=self.ACCENT,
                                        font=self.f_label, bd=0, highlightthickness=0,
                                        command=self.toggle_pitch, cursor="hand2")
        self.chk_pitch.pack(side="right")

        scroll_wrap = tk.Frame(speed_card, bg=self.BG_CARD)
        scroll_wrap.pack(fill="both", expand=True, padx=16, pady=(0, 12))

        self.canvas_speed = tk.Canvas(scroll_wrap, bg=self.BG_CARD,
                                      highlightthickness=0, bd=0, height=150)
        sb = tk.Scrollbar(scroll_wrap, orient="vertical", command=self.canvas_speed.yview)
        self.frame_speed = tk.Frame(self.canvas_speed, bg=self.BG_CARD)
        self.frame_speed.bind(
            "<Configure>",
            lambda e: self.canvas_speed.configure(scrollregion=self.canvas_speed.bbox("all"))
        )
        self.canvas_speed.create_window((0, 0), window=self.frame_speed, anchor="nw")
        self.canvas_speed.configure(yscrollcommand=sb.set)
        self.canvas_speed.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        def _on_wheel(e):
            self.canvas_speed.yview_scroll(int(-1 * (e.delta / 120)), "units")
        self.canvas_speed.bind_all("<MouseWheel>", _on_wheel)

        self.speed_buttons = {}
        for opt in self.speed_options:
            b = tk.Button(
                self.frame_speed, text=opt,
                bg=self.BG_INPUT, fg=self.FG_TEXT,
                font=self.f_label, anchor="w", padx=12, pady=8,
                relief="flat", bd=0, cursor="hand2",
                activebackground=self.BG_CARD_HI, activeforeground=self.ACCENT,
                command=lambda o=opt: self.set_speed(o)
            )
            b.pack(fill="x", pady=1)
            self.speed_buttons[opt] = b

        self.set_speed("1x", silent=True)

        # FOOTER
        tk.Label(self.container,
                 text="Right Shift = Start  |  Right Ctrl = Start Now  |  Left Shift = Stop",
                 fg=self.FG_MUTED, bg=self.BG_TOP, font=self.f_sub).pack(pady=(0, 12))

    def make_card(self, pad_bottom=8):
        wrap = tk.Frame(self.container, bg=self.BG_TOP)
        wrap.pack(fill="x", padx=24, pady=(6, pad_bottom))
        shadow = tk.Frame(wrap, bg="#050505")
        shadow.pack(fill="x")
        card = tk.Frame(shadow, bg=self.BG_CARD)
        card.pack(fill="x", padx=1, pady=1)
        return card

    def make_small_btn(self, parent, text, color, cmd, width=3):
        b = tk.Button(parent, text=text, bg=self.BG_INPUT, fg=color,
                      font=self.f_btn_small, width=width, relief="flat", bd=0,
                      cursor="hand2",
                      activebackground=self.BG_CARD_HI, activeforeground=color,
                      command=cmd)
        b.pack(side="left", padx=3)
        return b

    def add_hover(self, widget, normal_bg, hover_bg):
        widget.bind("<Enter>", lambda e: widget.config(bg=hover_bg))
        widget.bind("<Leave>", lambda e: widget.config(bg=normal_bg))

    def adjust_timing(self, d):
        Config.TIMING_OFFSET_MS += d

    def adjust_start(self, d):
        Config.START_OFFSET_MS = max(0, Config.START_OFFSET_MS + d)

    def reset_start(self):
        Config.START_OFFSET_MS = 0

    def toggle_pitch(self):
        Config.PITCH_LOCK = self.pitch_var.get()

    def set_speed(self, option, silent=False):
        for o, b in self.speed_buttons.items():
            b.config(bg=self.BG_INPUT, fg=self.FG_TEXT)

        if option == "Custom":
            val = simpledialog.askfloat("Custom speed", "Enter speed multiplier:",
                                        minvalue=0.1, maxvalue=5.0,
                                        initialvalue=Config.SPEED)
            if val is None:
                return
            Config.SPEED = float(val)
            self.speed_buttons["Custom"].config(text=f"Custom: {Config.SPEED:.2f}x")
        else:
            Config.SPEED = float(option.replace("x", ""))
            self.speed_buttons["Custom"].config(text="Custom speed")

        self.speed_buttons[option].config(bg=self.BG_CARD_HI, fg=self.ACCENT)
        self.lbl_speed.config(text=f"{Config.SPEED:.2f}x")

    def pick_file(self):
        path = filedialog.askopenfilename(
            title="Select Rhythia map",
            filetypes=[("Rhythia Map", "*.sspm"), ("All files", "*.*")]
        )
        if path:
            Config.MAP_PATH = path
            Config.NOTES, Config.SONG_DURATION_MS = load_sspm(path)
            self.lbl_notes.config(text=str(len(Config.NOTES)))

    def bind_hotkeys(self):
        threading.Thread(target=self._hotkey_listener, daemon=True).start()

    def _hotkey_listener(self):
        while True:
            if keyboard.is_pressed(Config.TOGGLE_UI_KEY):
                self.after(0, self.toggle_ui)
                time.sleep(0.4)
            time.sleep(0.05)

    def toggle_ui(self):
        if self.visible:
            self.fade_out()
        else:
            self.fade_in()

    def fade_in(self):
        self.deiconify()
        self.attributes("-alpha", 0.0)
        self.visible = True
        for i in range(0, 21):
            self.attributes("-alpha", i * 0.048)
            self.update()
            time.sleep(0.008)

    def fade_out(self):
        for i in range(20, -1, -1):
            self.attributes("-alpha", i * 0.048)
            self.update()
            time.sleep(0.008)
        self.withdraw()
        self.visible = False

    def animate_status(self):
        if Config.IS_RUNNING:
            r = 4 + (int(time.time() * 4) % 2) * 2
            self.dot.coords(self.dot_id, 6 - r, 6 - r, 6 + r, 6 + r)
            self.dot.itemconfig(self.dot_id, fill=self.GREEN)
        else:
            self.dot.coords(self.dot_id, 2, 2, 10, 10)
            self.dot.itemconfig(self.dot_id, fill=self.BLUE)
        self.after(150, self.animate_status)

    def update_status(self):
        if Config.IS_RUNNING:
            self.lbl_mode.config(text="PLAYING", fg=self.GREEN)
        else:
            self.lbl_mode.config(text="IDLE", fg=self.BLUE)

        self.lbl_timing.config(text=f"{Config.TIMING_OFFSET_MS:+d} ms"
                                    if Config.TIMING_OFFSET_MS != 0 else "0 ms")
        self.lbl_start.config(text=f"{Config.START_OFFSET_MS} ms")

        if Config.IS_RUNNING and Config.SONG_DURATION_MS > 0:
            elapsed = time.time() * 1000 - self.player.song_start_ms
            elapsed = max(0, min(elapsed, Config.SONG_DURATION_MS))
            pct = elapsed / Config.SONG_DURATION_MS

            w = self.progress_canvas.winfo_width()
            if w > 1:
                self.progress_canvas.coords(self.progress_bar, 0, 0, int(w * pct), 6)

            self.lbl_time.config(
                text=f"{self.fmt_time(elapsed)} / {self.fmt_time(Config.SONG_DURATION_MS)}")
        else:
            self.lbl_time.config(text="00:00 / 00:00")
            self.progress_canvas.coords(self.progress_bar, 0, 0, 0, 6)

        self.after(80, self.update_status)

    def fmt_time(self, ms):
        s = int(ms / 1000)
        return f"{s // 60:02d}:{s % 60:02d}"


# ============================================================
#  MAIN
# ============================================================
if __name__ == "__main__":
    app = OverlayApp()
    app.mainloop()
