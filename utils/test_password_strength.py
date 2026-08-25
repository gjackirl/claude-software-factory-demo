from password_strength import check_strength


def test_password_strength():
    test_cases = [
        # (password, expected_strength)
        ("abc", "weak"),                        # too short, no variety
        ("password", "weak"),                   # 8 chars but only lowercase
        ("Password1", "medium"),                # 9 chars, upper + lower + digit
        ("p@ssw0rd", "medium"),                 # 8 chars, lower + digit + symbol
        ("C0mpl3x!Pass#", "strong"),            # 13 chars, all four types
        ("Tr0ub4dor&3", "medium"),              # 11 chars, all four types but under 12-char strong threshold
        ("short", "weak"),                      # too short
        ("ALLUPPERCASE123!", "strong"),         # 16 chars, upper + digit + symbol
    ]

    all_passed = True
    for password, expected in test_cases:
        result = check_strength(password)
        status = "PASS" if result == expected else "FAIL"
        if status == "FAIL":
            all_passed = False
        print(f"[{status}] check_strength({password!r}) = {result!r} (expected {expected!r})")

    if all_passed:
        print("\nAll tests passed!")
    else:
        print("\nSome tests failed.")


if __name__ == "__main__":
    test_password_strength()
