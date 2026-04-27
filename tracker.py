import threading

# Cap on how many samples we keep so the graph never gets sluggish.
# When we hit the cap, we downsample by half (keep every other point),
# which preserves the overall shape without growing forever.
MAX_SAMPLES = 600


class Tracker:
    def __init__(self):
        self._lock = threading.Lock()
        self.data = []

    def add(self, attempt, time_elapsed):
        with self._lock:
            self.data.append((time_elapsed, attempt))
            if len(self.data) > MAX_SAMPLES:
                # Downsample: keep every second point. Keeps memory & redraw cost flat.
                self.data = self.data[::2]

    def snapshot(self):
        with self._lock:
            return list(self.data)

    def reset(self):
        with self._lock:
            self.data = []
