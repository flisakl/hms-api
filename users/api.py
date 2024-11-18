from ninja import Router, Form
from ninja.errors import ValidationError

from .schemas import RegistrationSchema, LoginSchemaOut
from .models import User
from helpers import make_errors

router = Router(tags=['users'])


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
