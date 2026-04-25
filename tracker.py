import threading


class Tracker:
    def __init__(self):
        self._lock = threading.Lock()
        self.data = []

    def add(self, attempt, time_elapsed):
        with self._lock:
            self.data.append((time_elapsed, attempt))

    def snapshot(self):
        with self._lock:
            return list(self.data)

    def reset(self):
        with self._lock:
            self.data = []
