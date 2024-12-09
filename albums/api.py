from django.db.models import Count
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
from schemas import AlbumArtist, AlbumSchemaIn, AlbumFilter, AlbumFull, AlbumArtistTrackCount
from .models import Album


staff_auth = AsyncHttpBearer(is_staff=True)
router = Router(tags=['Albums'], auth=staff_auth)


@router.post('', response={201: AlbumArtistTrackCount})
async def create_album(request, data: Form[AlbumSchemaIn], cover: UploadedFile = File(None)):
    errors = []
    attrs = data.dict(exclude_unset=True)

    try:
        # Check if artist exists
        await Artist.objects.aget(pk=data.artist_id)

        # Validate image
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


@router.get('', response=List[AlbumArtistTrackCount], auth=None)
@paginate
async def get_albums(request, filters: Query[AlbumFilter]):
    qs = Album.objects.select_related('artist').annotate(track_count=Count('track'))
    return await sync_to_async(list)(filters.filter(qs))


@router.get('/{int:albumID}', response=AlbumFull, auth=None)
async def get_album(request, albumID: int):
    qs = Album.objects.prefetch_related('artist', 'track_set', 'track_set__artists')
    album = await aget_object_or_404(qs, pk=albumID)
    return album
