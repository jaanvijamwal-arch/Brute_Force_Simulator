import string


def build_charset(lowercase=True, uppercase=True, digits=True, special=True):
    chars = ""
    if lowercase:
        chars += string.ascii_lowercase
    if uppercase:
        chars += string.ascii_uppercase
    if digits:
        chars += string.digits
    if special:
        chars += "!@#$%^&*"
    return chars


def get_charset():
    return string.ascii_lowercase + string.digits
