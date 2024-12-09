from ninja import Router, Form, Query, File
from ninja.pagination import paginate
from ninja.files import UploadedFile
from ninja.errors import ValidationError
from django.db import IntegrityError
from django.utils.translation import gettext_lazy as _
from django.shortcuts import aget_object_or_404
from typing import List, Optional
from asgiref.sync import sync_to_async

from users.api import AsyncHttpBearer
from artists.models import Artist
from helpers import make_errors, image_is_valid
from .schemas import AlbumSchema, AlbumSchemaIn
from .models import Album


staff_auth = AsyncHttpBearer(is_staff=True)
router = Router(tags=['Albums'], auth=staff_auth)


@router.post('', response={201: AlbumSchema})
async def create_album(request, data: Form[AlbumSchemaIn], cover: UploadedFile = File(None)):
    errors = []
    attrs = data.dict(exclude_unset=True)

    try:
        # Check if artist exists
        await Artist.objects.aget(pk=data.artist_id)

        if cover and not image_is_valid(cover):
            errors.append(make_errors('image', _('File is not an image')))
        else:
            album = Album(cover=cover, **attrs)
            await album.asave()
            return 201, await Album.objects.select_related('artist').aget(pk=album.pk)

    except Artist.DoesNotExist:
        errors.append(make_errors('artist_id', _('Artist does not exist')))

    except IntegrityError:
        errors.append(make_errors('name', _("Artist's album with given name already exists")))
    raise ValidationError(errors)
