import csv
import os
import sys
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox

from results_logger import LOG_FILE, FIELDS


# ---- colors (kept in sync with ui.py palette) ----
BG_DARK = "#0a1929"
BG_PANEL = "#0f2540"
BG_INPUT = "#0a1f38"
BORDER = "#1f3a57"
TEXT = "#e6f1ff"
TEXT_DIM = "#7faed1"
ACCENT = "#3aa0ff"
SUCCESS = "#22c55e"
DANGER = "#ef4444"
SLATE = "#1e293b"

FONT_TITLE = ("Segoe UI", 14, "bold")
FONT_LABEL = ("Segoe UI", 10)
FONT_BUTTON = ("Segoe UI", 10, "bold")


COLUMN_LABELS = {
    "timestamp": "When",
    "password": "Password",
    "password_length": "Len",
    "charset_size": "Charset",
    "min_length": "Min",
    "max_length": "Max",
    "attempts": "Attempts",
    "elapsed_seconds": "Time (s)",
    "attempts_per_second": "Speed (/s)",
    "status": "Status",
}

COLUMN_WIDTHS = {
    "timestamp": 150,
    "password": 140,
    "password_length": 50,
    "charset_size": 70,
    "min_length": 50,
    "max_length": 50,
    "attempts": 110,
    "elapsed_seconds": 90,
    "attempts_per_second": 110,
    "status": 90,
}


def open_file_externally(path):
    """Open the CSV in the system's default application (Excel, Numbers, etc.)."""
    if not os.path.exists(path):
        messagebox.showinfo(
            "No results yet",
            "The results file hasn't been created yet.\n"
            "Run an attack first, then try again."
        )
        return
    try:
        if sys.platform.startswith("win"):
            os.startfile(path)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])
    except Exception as e:
        messagebox.showerror("Could not open file", str(e))


class ResultsViewer(tk.Toplevel):
    """A styled window that shows results.csv as a sortable table."""

    def __init__(self, master, file_path=LOG_FILE):
        super().__init__(master)
        self.file_path = file_path
        self.title("Attack Results History")
        self.geometry("980x520")
        self.minsize(820, 420)
        self.configure(bg=BG_DARK)

        self._sort_state = {}  # column -> bool (descending?)
        self._build_ui()
        self.refresh()

    # ---------- layout ----------
    def _build_ui(self):
        # Header
        header = tk.Frame(self, bg=BG_DARK)
        header.pack(fill="x", padx=14, pady=(14, 8))

        tk.Label(header, text="\U0001F4D1  Attack Results History",
                 bg=BG_DARK, fg=ACCENT, font=FONT_TITLE).pack(side="left")

        # Path label (so the user knows where the file lives)
        path_row = tk.Frame(self, bg=BG_DARK)
        path_row.pack(fill="x", padx=14)
        tk.Label(path_row, text="File:", bg=BG_DARK, fg=TEXT_DIM,
                 font=FONT_LABEL).pack(side="left")
        self.lbl_path = tk.Label(
            path_row, text=os.path.abspath(self.file_path),
            bg=BG_DARK, fg=TEXT, font=("Consolas", 9), anchor="w"
        )
        self.lbl_path.pack(side="left", padx=(6, 0), fill="x", expand=True)

        # Buttons row
        btns = tk.Frame(self, bg=BG_DARK)
        btns.pack(fill="x", padx=14, pady=(8, 8))

        tk.Button(
            btns, text="\u21BB  Refresh", command=self.refresh,
            bg=ACCENT, fg="white", activebackground="#1976d2",
            activeforeground="white", font=FONT_BUTTON,
            relief="flat", bd=0, cursor="hand2", padx=12, pady=6
        ).pack(side="left")

        tk.Button(
            btns, text="\U0001F4C2  Open CSV in Excel",
            command=lambda: open_file_externally(self.file_path),
            bg=SUCCESS, fg="white", activebackground="#16a34a",
            activeforeground="white", font=FONT_BUTTON,
            relief="flat", bd=0, cursor="hand2", padx=12, pady=6
        ).pack(side="left", padx=(8, 0))

        tk.Button(
            btns, text="\U0001F5D1  Clear Results", command=self.clear,
            bg=DANGER, fg="white", activebackground="#dc2626",
            activeforeground="white", font=FONT_BUTTON,
            relief="flat", bd=0, cursor="hand2", padx=12, pady=6
        ).pack(side="left", padx=(8, 0))

        self.lbl_count = tk.Label(btns, text="0 runs", bg=BG_DARK,
                                  fg=TEXT_DIM, font=FONT_LABEL)
        self.lbl_count.pack(side="right")

        # Table (Treeview) inside a styled frame
        table_wrap = tk.Frame(self, bg=BG_PANEL, highlightthickness=1,
                              highlightbackground=BORDER)
        table_wrap.pack(fill="both", expand=True, padx=14, pady=(0, 14))

        style = ttk.Style(self)
        # Use 'clam' so colors actually apply on Windows
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure(
            "Results.Treeview",
            background=BG_INPUT,
            fieldbackground=BG_INPUT,
            foreground=TEXT,
            rowheight=24,
            bordercolor=BORDER,
            borderwidth=0,
            font=("Consolas", 10),
        )
        style.configure(
            "Results.Treeview.Heading",
            background=BG_PANEL,
            foreground=ACCENT,
            font=("Segoe UI", 10, "bold"),
            relief="flat",
        )
        style.map(
            "Results.Treeview",
            background=[("selected", "#1976d2")],
            foreground=[("selected", "white")],
        )

        self.tree = ttk.Treeview(
            table_wrap, columns=FIELDS, show="headings",
            style="Results.Treeview"
        )
        for col in FIELDS:
            self.tree.heading(
                col, text=COLUMN_LABELS.get(col, col),
                command=lambda c=col: self._sort_by(c)
            )
            self.tree.column(
                col, width=COLUMN_WIDTHS.get(col, 100),
                anchor="w", stretch=False
            )

        # Row striping
        self.tree.tag_configure("odd", background=BG_INPUT)
        self.tree.tag_configure("even", background="#0d2944")
        self.tree.tag_configure("cracked", foreground=SUCCESS)
        self.tree.tag_configure("notfound", foreground=DANGER)

        vsb = ttk.Scrollbar(table_wrap, orient="vertical",
                            command=self.tree.yview)
        hsb = ttk.Scrollbar(table_wrap, orient="horizontal",
                            command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        table_wrap.rowconfigure(0, weight=1)
        table_wrap.columnconfigure(0, weight=1)

    # ---------- data ----------
    def _read_rows(self):
        if not os.path.exists(self.file_path):
            return []
        try:
            with open(self.file_path, "r", encoding="utf-8", newline="") as f:
                return list(csv.DictReader(f))
        except Exception as e:
            messagebox.showerror("Could not read CSV", str(e))
            return []

    def refresh(self):
        rows = self._read_rows()

        # Clear existing
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Newest first
        rows.reverse()

        for i, row in enumerate(rows):
            values = [row.get(col, "") for col in FIELDS]
            stripe = "even" if i % 2 == 0 else "odd"
            status_tag = (
                "cracked" if row.get("status") == "Cracked" else "notfound"
            )
            self.tree.insert(
                "", "end", values=values, tags=(stripe, status_tag)
            )

        self.lbl_count.config(
            text=f"{len(rows)} run{'s' if len(rows) != 1 else ''}"
        )
        self.lbl_path.config(text=os.path.abspath(self.file_path))

    def _sort_by(self, col):
        rows = [
            (self.tree.set(k, col), k) for k in self.tree.get_children("")
        ]
        descending = self._sort_state.get(col, False)

        def to_sortable(value):
            try:
                return float(value)
            except (TypeError, ValueError):
                return str(value).lower()

        rows.sort(key=lambda x: to_sortable(x[0]), reverse=descending)
        for index, (_, k) in enumerate(rows):
            self.tree.move(k, "", index)
            stripe = "even" if index % 2 == 0 else "odd"
            current_tags = list(self.tree.item(k, "tags"))
            current_tags = [t for t in current_tags if t not in ("odd", "even")]
            current_tags.append(stripe)
            self.tree.item(k, tags=current_tags)
        self._sort_state[col] = not descending

    def clear(self):
        if not messagebox.askyesno(
            "Clear results?",
            "This will permanently delete every saved run from the CSV file.\n"
            "Continue?"
        ):
            return
        try:
            if os.path.exists(self.file_path):
                os.remove(self.file_path)
        except Exception as e:
            messagebox.showerror("Could not clear", str(e))
            return
        self.refresh()
