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
        errors.append(make_errors(
            'name', _("Artist's album with given name already exists")))
    raise ValidationError(errors)


@router.get('', response=List[AlbumArtistTrackCount], auth=None)
@paginate
async def get_albums(request, filters: Query[AlbumFilter]):
    qs = Album.objects.select_related(
        'artist').annotate(track_count=Count('track'))
    return await sync_to_async(list)(filters.filter(qs))


@router.get('/{int:albumID}', response=AlbumFull, auth=None)
async def get_album(request, albumID: int):
    qs = Album.objects.prefetch_related(
        'artist', 'track_set', 'track_set__artists')
    album = await aget_object_or_404(qs, pk=albumID)
    return album


@router.put('/{int:albumID}', response=AlbumArtist)
async def update_album(request, albumID: int, data: Form[AlbumSchemaIn], cover: UploadedFile = File(None)):
    errors = []
    args = data.dict(exclude_unset=True)
    image_ok = cover is not None and image_is_valid(cover)
    try:
        artist = await Artist.objects.aget(pk=data.artist_id)
        album = await Album.objects.aget(pk=albumID)
        del args['artist_id']
        # Update existing album
        album.artist = artist
        for k, value in args.items():
            setattr(album, k, value)

        # Delete old picture and set new one
        if image_ok:
            await sync_to_async(album.cover.delete)(save=False)
            await sync_to_async(album.cover.save)(cover.name, cover)
        else:
            await album.asave()

    # If artist does not exist, there's no point in updating the resource
    except Artist.DoesNotExist:
        errors.append(make_errors('artist_id', _('Artist does not exist')))

    except Album.DoesNotExist:
        if image_ok:
            args['cover'] = cover
        album = await Album.objects.acreate(
            artist=artist, **args)

    except IntegrityError:
        errors.append(make_errors('name', _("Artist's album already exists")))

    if errors:
        raise ValidationError(errors)
    return album
