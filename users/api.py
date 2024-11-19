import logging
from ninja import Router, Form, Query
from ninja.errors import ValidationError
from ninja.security import HttpBearer
from django.conf import settings
from django.http import HttpRequest
from django.shortcuts import aget_object_or_404
from asgiref.sync import sync_to_async
from typing import Optional, Any, List

from .schemas import RegistrationSchema, LoginSchemaOut, UserSchema, UserFilter
from .models import User
from helpers import make_errors

router = Router(tags=['users'])
logger = logging.getLogger("django")


class AsyncHttpBearer(HttpBearer):
    def __init__(self, is_staff=None, is_superuser=None) -> None:
        self.staff = is_staff
        self.super = is_superuser
        return super().__init__()

    async def __call__(self, request: HttpRequest) -> Optional[Any]:
        headers = request.headers
        auth_value = headers.get(self.header)
        if not auth_value:
            return None
        parts = auth_value.split(" ")

        if parts[0].lower() != self.openapi_scheme:
            if settings.DEBUG:
                logger.error(f"Unexpected auth - '{auth_value}'")
            return None
        token = " ".join(parts[1:])
        return await self.authenticate(request, token)

    async def authenticate(self, request: HttpRequest, token: str):
        try:
            user = await User.objects.aget(token=token)
        except User.DoesNotExist:
            pass

        # If either of options has been specified we can return the user
        if self.staff == self.super and self.staff is None:
            return user

        if self.staff is not None and self.staff == user.is_staff:
            return user

        if self.super is not None and self.super == user.is_superuser:
            return user

        return None


@router.post('', response={201: LoginSchemaOut})
async def create_account(request, data: Form[RegistrationSchema]):
    user = User()
    ud = data.dict(exclude_unset=True)
    for k, value in ud.items():
        if k not in ['password1', 'password2']:
            setattr(user, k, value)

    user.set_password(data.password1)

    errors = []

    # Check if email address is not already taken
    tmp = await User.objects.filter(email=data.email).aexists()
    if tmp:
        errors.append(make_errors("email", "Email address is already taken"))

    # Check if username is not already taken
    tmp = await User.objects.filter(username=data.username).aexists()
    if tmp:
        errors.append(make_errors("username", "Username already taken"))

    if errors:
        raise ValidationError(errors)

    await user.asave()
    return 201, user


@router.get('', response=List[UserSchema], auth=AsyncHttpBearer(is_superuser=True))
async def get_users(request, filters: Query[UserFilter]):
    qs = User.objects.all()
    return await sync_to_async(list)(filters.filter(qs))


@router.get('/{int:user_id}', response=UserSchema, auth=AsyncHttpBearer(is_superuser=True))
async def get_user(request, user_id: int):
    return await aget_object_or_404(User, pk=user_id)
