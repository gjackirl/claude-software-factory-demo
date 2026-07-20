import re


def is_valid_email(email: str) -> bool:
    """Return True if email matches standard email format rules, False otherwise.

    Rules:
    - Must contain exactly one @ symbol
    - Domain part must contain at least one dot
    - No spaces allowed
    - Must not start or end with special characters (., @, -, _, +)
    """
    if not email or " " in email:
        return False

    special_chars = {".", "@", "-", "_", "+"}
    if email[0] in special_chars or email[-1] in special_chars:
        return False

    pattern = r"^[A-Za-z0-9][A-Za-z0-9._%+\-]*@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$"
    return bool(re.match(pattern, email))
