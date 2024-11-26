from ninja import Router, Form, Query, File
from ninja.pagination import paginate
from ninja.files import UploadedFile
from ninja.errors import ValidationError
from django.db import IntegrityError
from django.utils.translation import gettext_lazy as _
from django.shortcuts import aget_object_or_404
from typing import List
from asgiref.sync import sync_to_async

from .schemas import ArtistSchema, ArtistFilter, ArtistAndAlbumsSchema
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


@router.get('', response=List[ArtistSchema], auth=None)
@paginate
async def get_artists(request, filters: Query[ArtistFilter]):
    qs = Artist.objects.all()
    return await sync_to_async(list)(filters.filter(qs))


@router.get('/{int:artistID}', response=ArtistAndAlbumsSchema, auth=None)
async def get_artist(request, artistID: int):
    # TODO: Uncomment line below once Album model is defined
    # qs = Artist.objects.prefetch_related('album_set')
    qs = Artist.objects.all()
    return await aget_object_or_404(qs, pk=artistID)
