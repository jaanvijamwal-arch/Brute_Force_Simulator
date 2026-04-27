import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import queue

from brute_force import brute_force_attack
from charset import build_charset
from tracker import Tracker
from utils import format_time, format_int
from estimator import estimate_crack_time, estimate_total_space
from strength_checker import check_strength
from graph import Graph, HAS_MPL
from results_logger import log_result, LOG_FILE
from results_viewer import ResultsViewer, open_file_externally

if HAS_MPL:
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


# ---------- Color palette (matches the screenshot) ----------
BG_DARK = "#0a1929"
BG_PANEL = "#0f2540"
BG_CARD = "#0b1b2b"
BG_INPUT = "#0a1f38"
BORDER = "#1f3a57"
TEXT = "#e6f1ff"
TEXT_DIM = "#7faed1"
ACCENT = "#3aa0ff"
ACCENT_DARK = "#1976d2"
SUCCESS = "#22c55e"
SUCCESS_DARK = "#16a34a"
DANGER = "#ef4444"
DANGER_DARK = "#dc2626"
WARNING = "#facc15"
SLATE = "#1e293b"

FONT_TITLE = ("Segoe UI", 18, "bold")
FONT_SUBTITLE = ("Segoe UI", 10)
FONT_SECTION = ("Segoe UI", 11, "bold")
FONT_LABEL = ("Segoe UI", 10)
FONT_VALUE = ("Consolas", 11, "bold")
FONT_BUTTON = ("Segoe UI", 11, "bold")


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Brute Force Attack Simulator")
        self.root.geometry("1080x760")
        self.root.minsize(1000, 720)
        self.root.configure(bg=BG_DARK)

        self.tracker = Tracker()
        self.running = False
        self.paused = False
        self.start_time = None
        self.total_space = 0
        self.event_queue = queue.Queue()
        self._last_graph_draw = 0.0
        self._graph_redraw_interval = 5.0  # seconds — keep UI snappy on long runs

        # Char-set checkboxes
        self.var_lower = tk.BooleanVar(value=True)
        self.var_upper = tk.BooleanVar(value=True)
        self.var_digits = tk.BooleanVar(value=True)
        self.var_special = tk.BooleanVar(value=True)
        self.var_min_length = tk.IntVar(value=1)
        self.var_max_length = tk.IntVar(value=4)

        self._build_ui()
        self.root.after(50, self._poll_events)

    # ============================================================
    # LAYOUT
    # ============================================================
    def _build_ui(self):
        # Header
        self._build_header()

        body = tk.Frame(self.root, bg=BG_DARK)
        body.pack(fill="both", expand=True, padx=16, pady=(0, 12))
        body.columnconfigure(0, weight=1, uniform="col")
        body.columnconfigure(1, weight=1, uniform="col")
        body.rowconfigure(0, weight=1)

        left = tk.Frame(body, bg=BG_DARK)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        right = tk.Frame(body, bg=BG_DARK)
        right.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        self._build_input_section(left)
        self._build_charset_section(left)
        self._build_attack_options(left)
        self._build_action_buttons(left)

        self._build_progress_section(right)
        self._build_result_section(right)

        # Tip bar
        tip = tk.Frame(self.root, bg=BG_PANEL, highlightthickness=1,
                       highlightbackground=BORDER)
        tip.pack(fill="x", padx=16, pady=(0, 12))
        tk.Label(
            tip,
            text="  Tip: Longer passwords and more character types "
                 "increase the time required to crack.",
            bg=BG_PANEL, fg=TEXT_DIM, font=FONT_SUBTITLE, anchor="w"
        ).pack(fill="x", padx=10, pady=8)

    def _build_header(self):
        header = tk.Frame(self.root, bg=BG_DARK)
        header.pack(fill="x", padx=16, pady=(14, 12))

        icon = tk.Label(header, text="\U0001F512", bg=BG_DARK,
                        fg=ACCENT, font=("Segoe UI", 28))
        icon.pack(side="left", padx=(8, 12))

        text_frame = tk.Frame(header, bg=BG_DARK)
        text_frame.pack(side="left")
        tk.Label(text_frame, text="BRUTE FORCE ATTACK SIMULATOR",
                 bg=BG_DARK, fg=TEXT, font=FONT_TITLE).pack(anchor="w")
        tk.Label(text_frame,
                 text="Simulate and Understand Brute Force Password Attacks",
                 bg=BG_DARK, fg=ACCENT, font=FONT_SUBTITLE).pack(anchor="w")

    # ---------- Cards ----------
    def _make_card(self, parent, title, icon=""):
        card = tk.Frame(parent, bg=BG_PANEL, highlightthickness=1,
                        highlightbackground=BORDER, bd=0)
        card.pack(fill="x", pady=(0, 12))
        header = tk.Frame(card, bg=BG_PANEL)
        header.pack(fill="x", padx=14, pady=(10, 6))
        tk.Label(header, text=f"{icon}  {title}".strip(),
                 bg=BG_PANEL, fg=ACCENT,
                 font=FONT_SECTION).pack(anchor="w")
        body = tk.Frame(card, bg=BG_PANEL)
        body.pack(fill="x", padx=14, pady=(0, 12))
        return body

    # ---------- INPUT SECTION ----------
    def _build_input_section(self, parent):
        body = self._make_card(parent, "INPUT SECTION", "\U0001F464")

        tk.Label(body, text="Enter Password to Test:",
                 bg=BG_PANEL, fg=TEXT, font=FONT_LABEL).pack(anchor="w")

        self.entry = tk.Entry(
            body, show="\u25cf", bg=BG_INPUT, fg=TEXT,
            insertbackground=ACCENT, font=("Consolas", 13),
            relief="flat", highlightthickness=1,
            highlightbackground=ACCENT, highlightcolor=ACCENT
        )
        self.entry.pack(fill="x", pady=(6, 8), ipady=8)
        self.entry.bind("<KeyRelease>", self._on_password_change)

        info = tk.Frame(body, bg=BG_PANEL)
        info.pack(fill="x")
        tk.Label(info, text="Password Length:", bg=BG_PANEL, fg=TEXT,
                 font=FONT_LABEL).pack(side="left")
        self.lbl_length = tk.Label(info, text="0", bg=BG_PANEL,
                                   fg=ACCENT, font=FONT_VALUE)
        self.lbl_length.pack(side="left", padx=(6, 16))

        tk.Label(info, text="Strength:", bg=BG_PANEL, fg=TEXT,
                 font=FONT_LABEL).pack(side="left")
        self.lbl_strength = tk.Label(info, text="-", bg=BG_PANEL,
                                     fg=TEXT_DIM, font=FONT_VALUE)
        self.lbl_strength.pack(side="left", padx=(6, 0))

    # ---------- CHARSET ----------
    def _build_charset_section(self, parent):
        body = self._make_card(parent, "CHARACTER SET", "\u2699")
        opts = [
            ("Lowercase (a-z)", self.var_lower),
            ("Uppercase (A-Z)", self.var_upper),
            ("Numbers (0-9)", self.var_digits),
            ("Special Characters (!@#$%^&*)", self.var_special),
        ]
        for text, var in opts:
            row = tk.Frame(body, bg=BG_PANEL)
            row.pack(fill="x", pady=2)
            cb = tk.Checkbutton(
                row, text=text, variable=var, bg=BG_PANEL, fg=TEXT,
                activebackground=BG_PANEL, activeforeground=TEXT,
                selectcolor=BG_INPUT, font=FONT_LABEL, anchor="w",
                bd=0, highlightthickness=0,
                command=self._on_password_change
            )
            cb.pack(side="left", anchor="w")

    # ---------- ATTACK OPTIONS ----------
    def _build_attack_options(self, parent):
        body = self._make_card(parent, "ATTACK OPTIONS", "\u26A1")

        for label, var in [("Start From Length:", self.var_min_length),
                           ("Max Length:", self.var_max_length)]:
            row = tk.Frame(body, bg=BG_PANEL)
            row.pack(fill="x", pady=4)
            tk.Label(row, text=label, bg=BG_PANEL, fg=TEXT,
                     font=FONT_LABEL).pack(side="left")
            spin = tk.Spinbox(
                row, from_=1, to=12, textvariable=var, width=8,
                bg=BG_INPUT, fg=TEXT, font=FONT_VALUE,
                buttonbackground=BG_INPUT, relief="flat",
                insertbackground=ACCENT,
                highlightthickness=1, highlightbackground=BORDER,
                command=self._on_password_change
            )
            spin.pack(side="right")
            var.trace_add("write", lambda *a: self._on_password_change())

    # ---------- ACTION BUTTONS ----------
    def _build_action_buttons(self, parent):
        wrap = tk.Frame(parent, bg=BG_DARK)
        wrap.pack(fill="x")

        self.btn_start = tk.Button(
            wrap, text="\u25B6  START ATTACK", command=self.start_attack,
            bg=SUCCESS, fg="white", activebackground=SUCCESS_DARK,
            activeforeground="white", font=FONT_BUTTON,
            relief="flat", bd=0, cursor="hand2"
        )
        self.btn_start.pack(fill="x", ipady=10, pady=(0, 8))

        self.btn_pause = tk.Button(
            wrap, text="⏸  PAUSE", command=self.toggle_pause,
            bg=WARNING, fg="#0a1929", activebackground="#eab308",
            activeforeground="#0a1929", font=FONT_BUTTON,
            relief="flat", bd=0, cursor="hand2", state="disabled"
        )
        self.btn_pause.pack(fill="x", ipady=8, pady=(0, 8))

        row = tk.Frame(wrap, bg=BG_DARK)
        row.pack(fill="x")
        row.columnconfigure(0, weight=1)
        row.columnconfigure(1, weight=1)

        self.btn_reset = tk.Button(
            row, text="\u21BA  RESET", command=self.reset,
            bg=SLATE, fg=TEXT, activebackground="#334155",
            activeforeground=TEXT, font=FONT_BUTTON,
            relief="flat", bd=0, cursor="hand2"
        )
        self.btn_reset.grid(row=0, column=0, sticky="ew", ipady=8,
                            padx=(0, 4))

        self.btn_exit = tk.Button(
            row, text="\u2715  EXIT", command=self.root.destroy,
            bg=DANGER, fg="white", activebackground=DANGER_DARK,
            activeforeground="white", font=FONT_BUTTON,
            relief="flat", bd=0, cursor="hand2"
        )
        self.btn_exit.grid(row=0, column=1, sticky="ew", ipady=8,
                           padx=(4, 0))

    # ---------- PROGRESS ----------
    def _build_progress_section(self, parent):
        body = self._make_card(parent, "ATTACK PROGRESS", "\U0001F4CA")

        status_row = tk.Frame(body, bg=BG_PANEL)
        status_row.pack(fill="x", pady=(0, 10))

        # A chip-like badge so the status really pops.
        self._status_chip = tk.Frame(
            status_row, bg=SLATE, highlightthickness=1,
            highlightbackground=BORDER
        )
        self._status_chip.pack(side="left")
        self.lbl_status = tk.Label(
            self._status_chip, text="  IDLE  ", bg=SLATE, fg=TEXT_DIM,
            font=("Segoe UI", 12, "bold"), padx=10, pady=4
        )
        self.lbl_status.pack()

        self.lbl_percent = tk.Label(
            status_row, text="0%", bg=BG_PANEL, fg=ACCENT,
            font=("Consolas", 14, "bold")
        )
        self.lbl_percent.pack(side="right")

        # Progress bar (custom, no ttk theming pain)
        bar_bg = tk.Frame(body, bg=BG_INPUT, height=10,
                         highlightthickness=1, highlightbackground=BORDER)
        bar_bg.pack(fill="x")
        bar_bg.pack_propagate(False)
        self.bar_fill = tk.Frame(bar_bg, bg=ACCENT, height=10)
        self.bar_fill.place(x=0, y=0, relwidth=0, relheight=1)
        self._bar_bg = bar_bg

        # Stat grid
        grid = tk.Frame(body, bg=BG_PANEL)
        grid.pack(fill="x", pady=(14, 0))
        grid.columnconfigure(0, weight=1, uniform="g")
        grid.columnconfigure(1, weight=1, uniform="g")

        self.stat_current = self._make_stat(grid, "Current Attempt:", 0, 0)
        self.stat_attempts = self._make_stat(grid, "Attempts:", 0, 1, fg=WARNING)
        self.stat_time = self._make_stat(grid, "Time Elapsed:", 1, 0,
                                         fg=SUCCESS, mono=True)
        self.stat_speed = self._make_stat(grid, "Attempts Per Second:", 1, 1,
                                          fg=ACCENT)

        # Estimate row
        est = tk.Frame(body, bg=BG_PANEL)
        est.pack(fill="x", pady=(14, 0))
        tk.Label(est, text="Estimated Time:", bg=BG_PANEL, fg=TEXT,
                 font=FONT_LABEL).pack(side="left")
        self.lbl_est_time = tk.Label(est, text="-", bg=BG_PANEL,
                                     fg=TEXT_DIM, font=FONT_VALUE)
        self.lbl_est_time.pack(side="left", padx=(6, 18))
        tk.Label(est, text="Search Space:", bg=BG_PANEL, fg=TEXT,
                 font=FONT_LABEL).pack(side="left")
        self.lbl_est_space = tk.Label(est, text="-", bg=BG_PANEL,
                                      fg=TEXT_DIM, font=FONT_VALUE)
        self.lbl_est_space.pack(side="left", padx=(6, 0))

        # Optional graph
        if HAS_MPL:
            self.graph = Graph()
            self.canvas = FigureCanvasTkAgg(self.graph.fig, master=body)
            widget = self.canvas.get_tk_widget()
            widget.pack(fill="both", expand=True, pady=(14, 0))
        else:
            self.graph = None
            self.canvas = None

    def _make_stat(self, parent, label, row, col, fg=TEXT, mono=False):
        wrap = tk.Frame(parent, bg=BG_PANEL)
        wrap.grid(row=row, column=col, sticky="ew", padx=4, pady=4)
        tk.Label(wrap, text=label, bg=BG_PANEL, fg=TEXT_DIM,
                 font=FONT_SUBTITLE, anchor="w").pack(fill="x")
        box = tk.Frame(wrap, bg=BG_INPUT, highlightthickness=1,
                       highlightbackground=BORDER)
        box.pack(fill="x", pady=(2, 0))
        font = ("Consolas", 12, "bold") if mono else FONT_VALUE
        lbl = tk.Label(box, text="-", bg=BG_INPUT, fg=fg, font=font,
                       anchor="w", padx=10, pady=8)
        lbl.pack(fill="x")
        return lbl

    # ---------- RESULTS ----------
    def _build_result_section(self, parent):
        body = self._make_card(parent, "RESULTS", "\U0001F3C6")

        self.result_box = tk.Frame(body, bg=BG_PANEL,
                                   highlightthickness=1,
                                   highlightbackground=BORDER)
        self.result_box.pack(fill="x", pady=4)

        top = tk.Frame(self.result_box, bg=BG_PANEL)
        top.pack(fill="x", padx=12, pady=(12, 4))
        self.lbl_result_icon = tk.Label(top, text="\u25CB", bg=BG_PANEL,
                                        fg=TEXT_DIM,
                                        font=("Segoe UI", 22, "bold"))
        self.lbl_result_icon.pack(side="left", padx=(0, 10))
        self.lbl_result_title = tk.Label(top, text="Awaiting attack...",
                                         bg=BG_PANEL, fg=TEXT_DIM,
                                         font=("Segoe UI", 13, "bold"))
        self.lbl_result_title.pack(side="left")

        details = tk.Frame(self.result_box, bg=BG_PANEL)
        details.pack(fill="x", padx=18, pady=(4, 14))
        self.lbl_r_password = self._make_result_row(details, "Password:")
        self.lbl_r_attempts = self._make_result_row(details, "Total Attempts:")
        self.lbl_r_time = self._make_result_row(details, "Time Taken:")
        self.lbl_r_speed = self._make_result_row(details, "Average Speed:")

        # ---- Results history actions ----
        actions = tk.Frame(body, bg=BG_PANEL)
        actions.pack(fill="x", pady=(8, 4))

        tk.Label(
            actions,
            text=f"All runs are saved to {LOG_FILE}",
            bg=BG_PANEL, fg=TEXT_DIM, font=FONT_SUBTITLE
        ).pack(anchor="w", padx=2, pady=(0, 6))

        btn_row = tk.Frame(body, bg=BG_PANEL)
        btn_row.pack(fill="x")
        btn_row.columnconfigure(0, weight=1)
        btn_row.columnconfigure(1, weight=1)

        tk.Button(
            btn_row, text="\U0001F4D1  VIEW HISTORY",
            command=self._open_history,
            bg=ACCENT, fg="white", activebackground=ACCENT_DARK,
            activeforeground="white", font=FONT_BUTTON,
            relief="flat", bd=0, cursor="hand2"
        ).grid(row=0, column=0, sticky="ew", ipady=8, padx=(0, 4))

        tk.Button(
            btn_row, text="\U0001F4C2  OPEN CSV",
            command=lambda: open_file_externally(LOG_FILE),
            bg=SLATE, fg=TEXT, activebackground="#334155",
            activeforeground=TEXT, font=FONT_BUTTON,
            relief="flat", bd=0, cursor="hand2"
        ).grid(row=0, column=1, sticky="ew", ipady=8, padx=(4, 0))

    def _make_result_row(self, parent, label):
        row = tk.Frame(parent, bg=BG_PANEL)
        row.pack(fill="x", pady=2)
        tk.Label(row, text=label, bg=BG_PANEL, fg=TEXT_DIM,
                 font=FONT_LABEL, width=16, anchor="w").pack(side="left")
        val = tk.Label(row, text="-", bg=BG_PANEL, fg=TEXT,
                       font=FONT_VALUE, anchor="w")
        val.pack(side="left")
        return val

    # ============================================================
    # EVENT HANDLERS
    # ============================================================
    def _on_password_change(self, *_):
        pwd = self.entry.get()
        self.lbl_length.config(text=str(len(pwd)))
        strength = check_strength(pwd)
        color = {
            "Weak": DANGER, "Medium": WARNING,
            "Strong": SUCCESS, "Very Strong": SUCCESS,
            "None": TEXT_DIM,
        }.get(strength, TEXT_DIM)
        self.lbl_strength.config(text=strength, fg=color)

        # Auto-fit max length to password length if smaller
        if pwd and self.var_max_length.get() < len(pwd):
            self.var_max_length.set(len(pwd))

        self._refresh_estimate()

    def _refresh_estimate(self):
        chars = build_charset(
            self.var_lower.get(), self.var_upper.get(),
            self.var_digits.get(), self.var_special.get()
        )
        if not chars:
            self.lbl_est_time.config(text="-")
            self.lbl_est_space.config(text="-")
            return

        min_len = max(1, self.var_min_length.get())
        max_len = max(min_len, self.var_max_length.get())

        space = estimate_total_space(len(chars), min_len, max_len)
        _, est_time = estimate_crack_time(chars, min_len, max_len)

        self.lbl_est_space.config(text=format_int(space))
        self.lbl_est_time.config(text=format_time(est_time))

    # ============================================================
    # ATTACK
    # ============================================================
    def start_attack(self):
        if self.running:
            return

        pwd = self.entry.get()
        if not pwd:
            messagebox.showerror("Error", "Please enter a password to test.")
            return

        # Build charset
        chars = build_charset(
            self.var_lower.get(),
            self.var_upper.get(),
            self.var_digits.get(),
            self.var_special.get()
        )

        if not chars:
            messagebox.showerror("Error", "Select at least one character set.")
            return

        # Length settings
        min_len = max(1, self.var_min_length.get())
        max_len = max(min_len, self.var_max_length.get())

        if max_len < len(pwd):
            messagebox.showwarning(
                "Range too small",
                "Max length is shorter than the password — it will not be found."
            )

        # 🔄 RESET STATE
        self.tracker.reset()
        self.start_time = time.time()
        self._last_graph_draw = 0.0
        self.running = True
        self.paused = False

        self.btn_pause.config(text="⏸  PAUSE", state="normal")

        # Store run parameters (used in logger)
        self._run_params = {
            "charset_size": len(chars),
            "min_length": min_len,
            "max_length": max_len,
        }

        # Estimate calculations
        self.total_space = estimate_total_space(len(chars), min_len, max_len)
        _, est_seconds = estimate_crack_time(chars, min_len, max_len)
        self._eta_seconds = est_seconds

        # 🟢 UI RESET
        self._set_status("Running...", fg="white", bg=ACCENT_DARK)
        self._set_progress(0)

        self.stat_current.config(text="-")
        self.stat_attempts.config(text="0")
        self.stat_time.config(text="00:00:00")
        self.stat_speed.config(text="0")

        self.lbl_result_icon.config(text="\u25CB", fg=TEXT_DIM)
        self.lbl_result_title.config(text="Attack in progress...", fg=TEXT_DIM)
        self.lbl_r_password.config(text="-", fg=TEXT)
        self.lbl_r_attempts.config(text="-", fg=TEXT)
        self.lbl_r_time.config(text="-", fg=TEXT)
        self.lbl_r_speed.config(text="-", fg=TEXT)

        self._refresh_estimate()

        # 🚀 START THREAD (NO LIMITS — manual stop only)
        thread = threading.Thread(
            target=brute_force_attack,
            args=(
                pwd,
                chars,
                self.tracker,
                self._on_progress,
                self._on_result,
                lambda: self.running,
                min_len,
                max_len,
                lambda: self.paused
            ),
            daemon=True
        )
        thread.start()

    def toggle_pause(self):
        if not self.running:
            return
        if self.paused:
            self.paused = False
            self.btn_pause.config(text="⏸  PAUSE")
            self._set_status("Running...", fg="white", bg=ACCENT_DARK)
        else:
            self.paused = True
            self.btn_pause.config(text="▶  RESUME")
            self._set_status("Paused", fg="#0a1929", bg=WARNING)

    def reset(self):
        self.running = False
        self.paused = False
        self.btn_pause.config(text="⏸  PAUSE", state="disabled")
        time.sleep(0.05)
        self.tracker.reset()
        self.entry.delete(0, tk.END)

        self._set_status("Idle")
        self._set_progress(0)
        self.stat_current.config(text="-")
        self.stat_attempts.config(text="-")
        self.stat_time.config(text="-")
        self.stat_speed.config(text="-")

        self.lbl_length.config(text="0")
        self.lbl_strength.config(text="-", fg=TEXT_DIM)
        self.lbl_est_time.config(text="-")
        self.lbl_est_space.config(text="-")

        self.lbl_result_icon.config(text="\u25CB", fg=TEXT_DIM)
        self.lbl_result_title.config(text="Awaiting attack...", fg=TEXT_DIM)
        self.lbl_r_password.config(text="-", fg=TEXT)
        self.lbl_r_attempts.config(text="-", fg=TEXT)
        self.lbl_r_time.config(text="-", fg=TEXT)
        self.lbl_r_speed.config(text="-", fg=TEXT)

        if self.graph:
            self.graph.clear()
            self.canvas.draw()

    # ---------- worker -> UI bridge (thread-safe via queue) ----------
    def _on_progress(self, attempts, current, elapsed):
        self.event_queue.put(("progress", attempts, current, elapsed))

    def _on_result(self, password, attempts, elapsed):
        self.event_queue.put(("result", password, attempts, elapsed))

    def _poll_events(self):
        try:
            while True:
                event = self.event_queue.get_nowait()
                kind = event[0]
                if kind == "progress":
                    _, attempts, current, elapsed = event
                    self._apply_progress(attempts, current, elapsed)
                elif kind == "result":
                    _, password, attempts, elapsed = event
                    self._apply_result(password, attempts, elapsed)
        except queue.Empty:
            pass
        self.root.after(50, self._poll_events)

    def _apply_progress(self, attempts, current, elapsed):
        if not self.running:
            return
        speed = int(attempts / elapsed) if elapsed > 0 else 0
        self.stat_current.config(text=current or "-")
        self.stat_attempts.config(text=format_int(attempts))
        self.stat_time.config(text=format_time(elapsed))
        self.stat_speed.config(text=format_int(speed))

        if self.total_space > 0:
            pct = min(100.0, attempts / self.total_space * 100.0)
            self._set_progress(pct)

        # Live remaining-time estimate based on actual measured speed
        if speed > 0 and self.total_space > 0:
            remaining = max(0, self.total_space - attempts) / speed
            self.lbl_est_time.config(text=format_time(remaining) + " left")

        if self.graph:
            now = time.time()
            if now - self._last_graph_draw >= self._graph_redraw_interval:
                self._last_graph_draw = now
                self.graph.plot(self.tracker)
                self.canvas.draw_idle()

    def _apply_result(self, password, attempts, elapsed):
        self.running = False
        self.paused = False
        self.btn_pause.config(text="⏸  PAUSE", state="disabled")

        speed = int(attempts / elapsed) if elapsed > 0 else 0
        self.stat_attempts.config(text=format_int(attempts))
        self.stat_time.config(text=format_time(elapsed))
        self.stat_speed.config(text=format_int(speed))

        # ✅ HANDLE ALL CASES
        if password == "Not Found":
            self._set_status("Not Found", fg="white", bg=DANGER_DARK)
            self.lbl_result_icon.config(text="\u2717", fg=DANGER)
            self.lbl_result_title.config(text="PASSWORD NOT FOUND", fg=DANGER)
            self.lbl_r_password.config(text=password, fg=DANGER)
            self._set_progress(0)

        elif "Stopped" in password:
            self._set_status("Stopped", fg="#0a1929", bg=WARNING)
            self.lbl_result_icon.config(text="\u26A0", fg=WARNING)
            self.lbl_result_title.config(text="ATTACK STOPPED BY USER", fg=WARNING)
            self.lbl_r_password.config(text=password, fg=WARNING)
            self._set_progress(0)

        else:
            self._set_status("Cracked", fg="white", bg=SUCCESS_DARK)
            self.lbl_result_icon.config(text="\u2714", fg=SUCCESS)
            self.lbl_result_title.config(text="PASSWORD CRACKED!", fg=SUCCESS)
            self.lbl_r_password.config(text=password, fg=SUCCESS)
            self._set_progress(100)

        self.lbl_r_attempts.config(text=format_int(attempts), fg=WARNING)
        self.lbl_r_time.config(text=format_time(elapsed), fg=SUCCESS)
        self.lbl_r_speed.config(
            text=f"{format_int(speed)} attempts/second",
            fg=ACCENT
        )

        # ✅ LOGGER FIX
        params = getattr(self, "_run_params", None) or {
            "charset_size": 0,
            "min_length": 0,
            "max_length": 0
        }

        if password == "Not Found":
            status = "Not Found"
        elif "Stopped" in password:
            status = "Stopped (User)"
        else:
            status = "Cracked"

        try:
            log_result(
                password=password,
                attempts=attempts,
                elapsed=elapsed,
                charset_size=params["charset_size"],
                min_length=params["min_length"],
                max_length=params["max_length"],
                status=status,
            )

            current = self.lbl_status.cget("text").strip()
            self.lbl_status.config(
                text=f"  {current} • LOGGED TO {LOG_FILE.upper()}  "
            )
        except Exception:
            pass

        if self.graph:
            self.graph.plot(self.tracker)
            self.canvas.draw_idle()

    def _set_status(self, text, fg=None, bg=None):
        if fg is None:
            fg = TEXT_DIM
        if bg is None:
            bg = SLATE
        chip_text = f"  {text.upper()}  "
        self.lbl_status.config(text=chip_text, fg=fg, bg=bg)
        self._status_chip.config(bg=bg)

    def _open_history(self):
        win = ResultsViewer(self.root, file_path=LOG_FILE)
        win.transient(self.root)
        win.lift()
        win.focus_force()

    def _set_progress(self, pct):
        pct = max(0.0, min(100.0, float(pct)))
        self.bar_fill.place(relwidth=pct / 100.0)
        if pct == 0:
            text = "0%"
        elif pct >= 1:
            text = f"{pct:.1f}%"
        elif pct >= 0.001:
            text = f"{pct:.3f}%"
        else:
            text = "<0.001%"
        self.lbl_percent.config(text=text)
