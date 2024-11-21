from ninja import Router, Form, Query, File
from ninja.files import UploadedFile
from ninja.errors import ValidationError
from django.db import IntegrityError
from django.utils.translation import gettext_lazy as _

from .schemas import ArtistSchema
from .models import Artist
from users.api import AsyncHttpBearer
from helpers import make_errors, image_is_valid


staff_auth = AsyncHttpBearer(is_staff=True)
router = Router(tags=['Artists'], auth=staff_auth)


@router.post('', response={201: ArtistSchema})
async def create_artist(request, name: Form[str], image: UploadedFile = File(None)):
    errors = []
    try:
        artist = Artist(name=name)
        # Validate the image if provided
        if image:
            if image_is_valid(image):
                artist.image = image
            else:
                errors.append(make_errors('image', _('File is not an image')))

    except IntegrityError:
        errors.append(make_errors('name', _('Artist already exists')))

    if errors:
        raise ValidationError(errors)
    else:
        await artist.asave()
        return 201, artist
