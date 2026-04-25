try:
    import matplotlib
    matplotlib.use("TkAgg")
    import matplotlib.pyplot as plt
    HAS_MPL = True
except Exception:
    HAS_MPL = False


class Graph:
    def __init__(self):
        if not HAS_MPL:
            self.fig = None
            self.ax = None
            return
        self.fig, self.ax = plt.subplots(figsize=(6, 2.5))
        self.fig.patch.set_facecolor("#0b1b2b")
        self.ax.set_facecolor("#0b1b2b")
        self._style_axes()

    def _style_axes(self):
        if not HAS_MPL:
            return
        for spine in self.ax.spines.values():
            spine.set_color("#1f3a57")
        self.ax.tick_params(colors="#7faed1")
        self.ax.title.set_color("#3aa0ff")
        self.ax.xaxis.label.set_color("#7faed1")
        self.ax.yaxis.label.set_color("#7faed1")

    def plot(self, tracker):
        if not HAS_MPL:
            return

        # Snapshot atomically — the worker thread may append while we read.
        data = tracker.snapshot() if hasattr(tracker, "snapshot") \
            else list(tracker.data)
        if not data:
            return

        t = [x[0] for x in data]
        a = [x[1] for x in data]

        self.ax.clear()
        self.ax.set_facecolor("#0b1b2b")
        self.ax.plot(t, a, color="#3aa0ff", linewidth=2)
        self.ax.fill_between(t, a, color="#3aa0ff", alpha=0.15)

        self.ax.set_title("Attempts vs Time")
        self.ax.set_xlabel("Time (s)")
        self.ax.set_ylabel("Attempts")
        self._style_axes()

    def clear(self):
        if not HAS_MPL:
            return
        self.ax.clear()
        self.ax.set_facecolor("#0b1b2b")
        self._style_axes()
