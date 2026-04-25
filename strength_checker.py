def check_strength(password):
    if not password:
        return "None"
    length = len(password)
    has_lower = any(c.islower() for c in password)
    has_upper = any(c.isupper() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(not c.isalnum() for c in password)

    variety = sum([has_lower, has_upper, has_digit, has_special])

    if length < 4 or (length < 6 and variety <= 1):
        return "Weak"
    if length < 8 or variety <= 2:
        return "Medium"
    if length >= 12 and variety >= 3:
        return "Very Strong"
    return "Strong"
