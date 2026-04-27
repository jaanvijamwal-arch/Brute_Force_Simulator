import csv
import os
from datetime import datetime

LOG_FILE = "results.csv"

FIELDS = [
    "timestamp",
    "password",
    "password_length",
    "charset_size",
    "min_length",
    "max_length",
    "attempts",
    "elapsed_seconds",
    "attempts_per_second",
    "status",
]


def log_result(password, attempts, elapsed, charset_size,
               min_length, max_length, status, file_path=LOG_FILE):
    """Append one attack result as a row in a CSV file."""
    speed = int(attempts / elapsed) if elapsed > 0 else 0
    row = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "password": password,
        "password_length": len(password) if password and status == "Cracked"
        else "",
        "charset_size": charset_size,
        "min_length": min_length,
        "max_length": max_length,
        "attempts": attempts,
        "elapsed_seconds": f"{elapsed:.4f}",
        "attempts_per_second": speed,
        "status": status,
    }

    write_header = not os.path.exists(file_path) \
        or os.path.getsize(file_path) == 0

    with open(file_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        if write_header:
            writer.writeheader()
        writer.writerow(row)
