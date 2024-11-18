from pydantic import ValidationError
import unittest

from users.schemas import RegistrationSchema


class TestUserSchemas(unittest.TestCase):

    def setUp(self):
        self.data = {
            'username': 'John',
            'email': 'john@email.com',
            'password1': 'Test1234',
            'password2': 'Test1234',
        }

    def test_username_holds_only_alphanumeric_values(self):
        RegistrationSchema(**self.data)
        with self.assertRaises(ValidationError) as ve:
            altered = self.data.copy()
            altered['username'] = '???John'
            RegistrationSchema(**altered)

        self.assertIn('only digits', str(ve.exception))

    def test_email_must_be_valid_address(self):
        with self.assertRaises(ValidationError):
            altered = self.data.copy()
            altered['email'] = 'junk@.com'
            RegistrationSchema(**altered)

    def test_password_must_contain_uppercase_letter(self):
        with self.assertRaises(ValidationError) as ve:
            altered = self.data.copy()
            altered['password1'] = 'test1234'
            RegistrationSchema(**altered)

        self.assertIn('uppercase', str(ve.exception))

    def test_password_must_contain_digit(self):
        with self.assertRaises(ValidationError) as ve:
            altered = self.data.copy()
            altered['password1'] = 'TTTTTTTT'
            RegistrationSchema(**altered)

        self.assertIn('digit', str(ve.exception))

    def test_password_must_be_at_least_8_characters_long(self):
        with self.assertRaises(ValidationError) as ve:
            altered = self.data.copy()
            altered['password1'] = '8TTTTTT'
            RegistrationSchema(**altered)

        self.assertIn('8', str(ve.exception))
