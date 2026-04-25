GUESSES_PER_SECOND = 5_000_000


def estimate_crack_time(charset, min_length, max_length,
                        guesses_per_second=GUESSES_PER_SECOND):
    if isinstance(charset, str):
        charset_size = len(charset)
    else:
        charset_size = len(list(charset))

    if charset_size == 0 or max_length < min_length:
        return 0, 0.0

    total_attempts = 0
    for length in range(min_length, max_length + 1):
        total_attempts += charset_size ** length

    average_attempts = total_attempts / 2 if total_attempts > 0 else 0
    estimated_time = average_attempts / guesses_per_second

    return int(average_attempts), estimated_time


def estimate_total_space(charset_size, min_length, max_length):
    total = 0
    for length in range(min_length, max_length + 1):
        total += charset_size ** length
    return total
