import re

from rest_framework import serializers


def validate_phone(value):
    """Phone may be blank; otherwise 7-15 digits (spaces, +, -, ( ) allowed)."""
    if value in (None, ''):
        return ''
    digits = re.sub(r'[\s\-().+]', '', str(value))
    if not digits.isdigit() or not 7 <= len(digits) <= 15:
        raise serializers.ValidationError('Phone number must contain 7-15 digits.')
    return value


def normalize_email(value):
    """Emails are case-insensitive; store lowercase."""
    return str(value).strip().lower()
