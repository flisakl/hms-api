from django.utils.translation import gettext_lazy as _
from django.test import TestCase

from users.models import User


def make_errors(field_name: str, msg):
    return {
        "loc": ["form", field_name],
        "msg": _(msg)
    }


class TestHelper(TestCase):
    async def create_user(self, username='john', password='test1234',
                          superuser=False, staff=False, email=None,
                          image=None):
        if not email:
            email = f"{username}@example.com"
        user = User(username=username, email=email,
                    is_staff=staff, is_superuser=superuser, avatar=image)
        user.set_password(password)
        await user.asave()
        return user

    async def create_staff_member(self, **kwargs):
        return await TestHelper.create_user(staff=True, **kwargs)

    def make_auth_header(self, user: User):
        return {
            'Authorization': f'Bearer {user.token}'
        }
