def check_strength(password: str) -> str:
    """Return 'weak', 'medium', or 'strong' based on password characteristics.

    Criteria:
    - Length: at least 8 chars for medium, at least 12 for strong
    - Character mix: uppercase, lowercase, digits, symbols
    """
    if not password:
        return "weak"

    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_symbol = any(not c.isalnum() for c in password)

    variety = sum([has_upper, has_lower, has_digit, has_symbol])
    length = len(password)

    if length >= 12 and variety >= 3:
        return "strong"
    elif length >= 8 and variety >= 2:
        return "medium"
    else:
        return "weak"
