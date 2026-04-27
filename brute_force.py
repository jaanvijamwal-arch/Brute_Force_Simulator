import itertools
import time
import traceback

# How often the worker tells the UI it is alive.
UI_UPDATE_INTERVAL = 0.15          # seconds — ~7 UI ticks/sec (gentle on Tk)
SAMPLE_INTERVAL_ATTEMPTS = 20_000  # check the clock every N attempts
FIRST_UPDATE_AFTER = 200           # force a very early first ping


def brute_force_attack(target, chars, tracker,
                       progress_callback, result_callback,
                       running_flag, min_length, max_length,
                       paused_flag=None):
    """
    Iterate from min_length up to max_length, trying every combination
    of `chars`. Reports progress via progress_callback and the final
    outcome via result_callback.

    progress_callback(attempts, current_guess, elapsed)
    result_callback(password_or_status, attempts, elapsed)
    """

    attempts = 0
    start = time.time()

    try:
        # Comparing the raw tuple itertools.product yields is much faster
        # than building a string for every guess. Only build the string
        # when we actually need it (for UI updates or the final match).
        target_tuple = tuple(target)

        last_ui_update = start
        last_sample_attempt = 0
        first_ping_sent = False
        join = ''.join  # local alias — small speedup in tight loop

        for length in range(min_length, max_length + 1):
            for guess in itertools.product(chars, repeat=length):
                if not running_flag():
                    return

                # Pause: idle the worker without quitting it.
                if paused_flag is not None and paused_flag():
                    pause_began = time.time()
                    while paused_flag() and running_flag():
                        time.sleep(0.1)
                    if not running_flag():
                        return
                    # Shift the timing baseline so the pause does not
                    # show up as a giant slowdown in the speed graph.
                    pause_skew = time.time() - pause_began
                    start += pause_skew
                    last_ui_update += pause_skew

                attempts += 1

                # --- found it? (fast tuple compare, no string build) ---
                if guess == target_tuple:
                    pwd = join(guess)
                    elapsed = time.time() - start
                    tracker.add(attempts, elapsed)
                    progress_callback(attempts, pwd, elapsed)
                    result_callback(pwd, attempts, elapsed)
                    return

                # --- early UI ping so the window stops looking frozen ---
                if not first_ping_sent and attempts >= FIRST_UPDATE_AFTER:
                    first_ping_sent = True
                    elapsed = time.time() - start
                    tracker.add(attempts, elapsed)
                    progress_callback(attempts, join(guess), elapsed)
                    last_ui_update = time.time()
                    last_sample_attempt = attempts
                    continue

                # --- regular sampled tick ---
                if attempts - last_sample_attempt >= SAMPLE_INTERVAL_ATTEMPTS:
                    now = time.time()
                    if now - last_ui_update >= UI_UPDATE_INTERVAL:
                        elapsed = now - start
                        tracker.add(attempts, elapsed)
                        progress_callback(attempts, join(guess), elapsed)
                        last_ui_update = now
                    last_sample_attempt = attempts

        elapsed = time.time() - start
        result_callback("Not Found", attempts, elapsed)

    except Exception:
        # Never let the worker thread die silently — always tell the UI
        # something happened so the result section gets updated.
        traceback.print_exc()
        elapsed = time.time() - start
        result_callback("Not Found", attempts, elapsed)
