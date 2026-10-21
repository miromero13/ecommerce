import secrets
import string


def generate_random_password(length: int = 12) -> str:
    """
    Generate a secure random password containing uppercase letters,
    lowercase letters, digits, and readable special characters.
    """
    if length < 8:
        length = 8

    # Ensure at least one of each required category
    lowercase = string.ascii_lowercase
    uppercase = string.ascii_uppercase
    digits = string.digits
    special = "!@#$%^&*-_=+"

    password_chars = [
        secrets.choice(lowercase),
        secrets.choice(uppercase),
        secrets.choice(digits),
        secrets.choice(special),
    ]

    all_chars = lowercase + uppercase + digits + special
    for _ in range(length - len(password_chars)):
        password_chars.append(secrets.choice(all_chars))

    secrets.SystemRandom().shuffle(password_chars)
    return "".join(password_chars)
