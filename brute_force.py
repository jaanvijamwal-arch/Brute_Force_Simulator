import itertools
import time
import traceback

UI_UPDATE_INTERVAL = 0.15
SAMPLE_INTERVAL_ATTEMPTS = 20_000
FIRST_UPDATE_AFTER = 200


def brute_force_attack(target, chars, tracker,
                       progress_callback, result_callback,
                       running_flag, min_length, max_length,
                       paused_flag=None):
    """
    Manual-stop version:
    - No automatic limits
    - User stops via UI (Reset/Stop)
    - Logs "Stopped (User)"
    """

    attempts = 0
    start = time.time()

    try:
        target_tuple = tuple(target)

        last_ui_update = start
        last_sample_attempt = 0
        first_ping_sent = False
        join = ''.join

        for length in range(min_length, max_length + 1):
            for guess in itertools.product(chars, repeat=length):

                # 🔴 USER STOP
                if not running_flag():
                    elapsed = time.time() - start
                    result_callback("Stopped (User)", attempts, elapsed)
                    return

                # ⏸ PAUSE
                if paused_flag is not None and paused_flag():
                    pause_began = time.time()
                    while paused_flag() and running_flag():
                        time.sleep(0.1)
                    if not running_flag():
                        elapsed = time.time() - start
                        result_callback("Stopped (User)", attempts, elapsed)
                        return

                    pause_skew = time.time() - pause_began
                    start += pause_skew
                    last_ui_update += pause_skew

                attempts += 1

                # ✅ PASSWORD FOUND
                if guess == target_tuple:
                    pwd = join(guess)
                    elapsed = time.time() - start
                    tracker.add(attempts, elapsed)
                    progress_callback(attempts, pwd, elapsed)
                    result_callback(pwd, attempts, elapsed)
                    return

                # ⚡ EARLY UI UPDATE
                if not first_ping_sent and attempts >= FIRST_UPDATE_AFTER:
                    first_ping_sent = True
                    elapsed = time.time() - start
                    tracker.add(attempts, elapsed)
                    progress_callback(attempts, join(guess), elapsed)
                    last_ui_update = time.time()
                    last_sample_attempt = attempts
                    continue

                # 🔁 REGULAR UPDATE
                if attempts - last_sample_attempt >= SAMPLE_INTERVAL_ATTEMPTS:
                    now = time.time()
                    if now - last_ui_update >= UI_UPDATE_INTERVAL:
                        elapsed = now - start
                        tracker.add(attempts, elapsed)
                        progress_callback(attempts, join(guess), elapsed)
                        last_ui_update = now
                    last_sample_attempt = attempts

        # ❌ NOT FOUND
        elapsed = time.time() - start
        result_callback("Not Found", attempts, elapsed)

    except Exception:
        traceback.print_exc()
        elapsed = time.time() - start
        result_callback("Not Found", attempts, elapsed)