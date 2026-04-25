import itertools
import time

UI_UPDATE_INTERVAL = 0.1
SAMPLE_INTERVAL_ATTEMPTS = 50_000


def brute_force_attack(target, chars, tracker,
                       progress_callback, result_callback,
                       running_flag, min_length, max_length):
    """
    Iterate from min_length up to max_length, trying every combination
    of `chars`. Reports progress via progress_callback and the final
    outcome via result_callback.

    progress_callback(attempts, current_guess, elapsed)
    result_callback(password_or_status, attempts, elapsed)
    """

    attempts = 0
    start = time.time()
    last_ui_update = start
    last_sample_attempt = 0

    for length in range(min_length, max_length + 1):
        for guess in itertools.product(chars, repeat=length):
            if not running_flag():
                return

            attempts += 1

            if attempts - last_sample_attempt >= SAMPLE_INTERVAL_ATTEMPTS:
                now = time.time()
                elapsed = now - start
                tracker.add(attempts, elapsed)
                last_sample_attempt = attempts

                if now - last_ui_update >= UI_UPDATE_INTERVAL:
                    pwd_preview = ''.join(guess)
                    progress_callback(attempts, pwd_preview, elapsed)
                    last_ui_update = now

            pwd = ''.join(guess)
            if pwd == target:
                elapsed = time.time() - start
                tracker.add(attempts, elapsed)
                progress_callback(attempts, pwd, elapsed)
                result_callback(pwd, attempts, elapsed)
                return

    elapsed = time.time() - start
    result_callback("Not Found", attempts, elapsed)
