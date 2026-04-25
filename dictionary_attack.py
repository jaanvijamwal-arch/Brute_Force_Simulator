import time


def dictionary_attack(target, filepath, update_callback, result_callback,
                      running_flag):
    attempts = 0
    start = time.time()

    try:
        with open(filepath) as f:
            for word in f:
                if not running_flag():
                    return

                guess = word.strip()
                attempts += 1

                if attempts % 500 == 0:
                    update_callback(attempts)

                if guess == target:
                    result_callback(guess, attempts, time.time() - start)
                    return
    except Exception:
        result_callback("Wordlist missing", 0, 0)
        return

    result_callback("Not Found", attempts, time.time() - start)
