import re
from general.enum import ValidationPatterns


def validate_email(email: str) -> bool:
    email_pattern = re.match(ValidationPatterns.VALIDATE_EMAIL, email)
    if email_pattern:
        return True
    return False
