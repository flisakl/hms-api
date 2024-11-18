from ninja import (
    ModelSchema, Schema
)
from django.utils.translation import gettext_lazy as _
from pydantic import field_validator, EmailStr, ValidationInfo
from typing import Optional

from .models import User


class PasswordMixin(Schema):
    password1: str
    password2: str

    @field_validator('password1')
    @classmethod
    def password_validation(cls, value: str) -> str:
        if len(value) < 8:
            # Translators: Error returned when provided password is to short
            msg = _('must be at least %(num)d characters long') % {'num': 8}
            raise ValueError(msg)
        has_digit = False
        has_uppercase_letter = False
        for char in value:
            if char.isdigit():
                has_digit = True
            if char.isupper():
                has_uppercase_letter = True

        if not has_digit:
            # Translators: Error returned when provided password does not contain X digits
            msg = _('must have at least %(num)d digit') % {'num': 1}
            raise ValueError(msg)
        if not has_uppercase_letter:
            # Translators: Error returned when provided password does not contain X uppercase letters
            msg = _('must have at least %(num)d uppercase letter') % {'num': 1}
            raise ValueError(msg)
        return value

    @field_validator('password2')
    @classmethod
    def passwords_matching(cls, value: str, vinfo: ValidationInfo):
        p1 = value
        p2 = vinfo.data.get('password1')

        if p1 != p2:
            # Translators: Error returned when provided username is incorrect
            raise ValueError(_('passwords do not match'))
        return p1


class RegistrationSchema(PasswordMixin):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: str
    email: EmailStr

    @field_validator('username')
    @classmethod
    def contains_only_letters_and_digits(cls, value: str):
        for letter in value:
            if not letter.isalnum():
                # Translators: Error returned when provided username is incorrect
                msg = _('must contain only digits and letters')
                raise ValueError(msg)
        return value


class UserSchema(ModelSchema):
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'avatar', 'is_superuser', 'is_staff'
        ]


class LoginSchemaOut(UserSchema):
    token: str
