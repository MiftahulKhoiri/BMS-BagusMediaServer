import re

PASSWORD_MIN_LENGTH = 8
_username_re = re.compile(r'^[A-Za-z0-9_]{3,32}$')

def valid_username(username):
    return bool(username and _username_re.match(username))

def valid_password(password):
    return bool(password and isinstance(password, str) and len(password) >= PASSWORD_MIN_LENGTH)