import logging
from ninja import Router, Form, Query, File
from ninja.errors import ValidationError
from ninja.security import HttpBearer
from ninja.files import UploadedFile
from django.db.models import Q
from django.conf import settings
from django.http import HttpRequest
from django.shortcuts import aget_object_or_404
from django.utils.translation import gettext_lazy as _
from asgiref.sync import sync_to_async
from typing import Optional, Any, List

from .schemas import (
    RegistrationSchema, LoginSchemaOut, UserSchema,
    UserFilter, UserUpdateSchema, PasswordChangeSchema,
    RoleSchema, LoginSchemaIn
)
from .models import User
from helpers import make_errors, image_is_valid

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
            return

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


@router.patch('', response=LoginSchemaOut, auth=AsyncHttpBearer())
async def update_user(request, data: Form[UserUpdateSchema], avatar:
                      UploadedFile = File(None)):
    data = data.dict(exclude_unset=True)
    user = request.auth

    # Set attributes
    for k, value in data.items():
        setattr(user, k, value)

    if avatar:
        # Check if provided image is valid
        if not image_is_valid(avatar):
            raise ValidationError([
                make_errors("avatar", _("File is not a valid image"))
            ])
        if user.avatar:
            await sync_to_async(user.avatar.delete)(save=False)
        await sync_to_async(user.avatar.save)(avatar.name, avatar, save=False)

    await user.asave()
    return user


@router.delete('', auth=AsyncHttpBearer(), response={204: None})
async def delete_account(request):
    user = request.auth

    # Delete user's avatar
    if (user.avatar):
        await sync_to_async(user.avatar.delete)(save=False)

    await user.adelete()
    return 204, None


@router.post('/password-change', auth=AsyncHttpBearer(), response=LoginSchemaOut)
async def change_password(request, data: Form[PasswordChangeSchema]):
    user = request.auth
    errors = []

    # Check if `old_password` matches current
    if not user.check_password(data.old_password):
        errors.append(
            make_errors('old_password', _('Old password is invalid'))
        )
    else:
        # No point changing the password to the same one
        if data.old_password == data.password1:
            errors.append(
                make_errors('old_password', _(
                    'New password can not be the same'))
            )
        else:
            user.set_password(data.password1)
            await user.asave()
            return user

    if errors:
        raise ValidationError(errors)


@router.post('/{int:user_id}', auth=AsyncHttpBearer(is_superuser=True),
             response=UserSchema)
async def update_role(request, user_id: int, data: Form[RoleSchema]):
    user = await aget_object_or_404(User, pk=user_id)
    user.is_superuser = data.is_superuser
    user.is_staff = data.is_staff
    await user.asave()
    return 200, user


@router.post('/login', response=LoginSchemaOut)
async def login(request, data: Form[LoginSchemaIn]):
    errors = []
    try:
        user = await User.objects.aget(
            Q(username=data.username) | Q(email=data.username))

        if user.check_password(data.password):
            return user

        errors.append(
            make_errors('password', _('Invalid password'))
        )

    except User.DoesNotExist:
        errors.append(
            make_errors('password', _('Wrong username or email address'))
        )

    if errors:
        raise ValidationError(errors)


@router.patch('/generate-token', auth=AsyncHttpBearer(), response=LoginSchemaOut)
async def generate_token(request):
    user = request.auth
    user._generate_token()
    await user.asave()
    return user
