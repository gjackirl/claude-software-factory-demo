from email_validator import is_valid_email

test_cases = [
    # (email, expected_result, description)
    ("user@example.com", True, "standard valid email"),
    ("firstname.lastname@domain.org", True, "dots in local part"),
    ("user+tag@mail.example.co.uk", True, "plus tag and subdomain"),
    ("user123@sub.domain.io", True, "numbers and subdomain"),
    ("a@b.co", True, "minimal valid email"),
    ("plainaddress", False, "missing @ and domain"),
    ("@nodomain.com", False, "starts with @"),
    ("user@", False, "missing domain"),
    ("user @example.com", False, "space in email"),
    (".user@example.com", False, "starts with dot"),
    ("user@example.com.", False, "ends with dot"),
    ("user@@example.com", False, "double @"),
    ("user@domain", False, "domain has no dot"),
    ("", False, "empty string"),
]

passed = 0
failed = 0

for email, expected, description in test_cases:
    result = is_valid_email(email)
    status = "PASS" if result == expected else "FAIL"
    if status == "PASS":
        passed += 1
    else:
        failed += 1
    print(f"[{status}] {description!r}: is_valid_email({email!r}) = {result} (expected {expected})")

print(f"\n{passed}/{passed + failed} tests passed.")
