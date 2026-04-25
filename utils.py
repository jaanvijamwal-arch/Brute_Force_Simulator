def format_time(seconds):
    if seconds is None:
        return "-"
    if seconds < 1:
        return f"{seconds*1000:.0f} ms"
    if seconds < 60:
        return f"{seconds:.2f} sec"
    if seconds < 3600:
        m = int(seconds // 60)
        s = seconds - m * 60
        return f"{m:02d}:{s:05.2f}"
    if seconds < 86400:
        h = int(seconds // 3600)
        m = int((seconds - h * 3600) // 60)
        s = int(seconds - h * 3600 - m * 60)
        return f"{h:02d}:{m:02d}:{s:02d}"
    days = seconds / 86400
    if days < 365:
        return f"{days:.1f} days"
    years = days / 365
    return f"{years:.1f} years"


def format_int(n):
    return f"{int(n):,}"
