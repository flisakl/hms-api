from django.db import models
from ninja import Router, Form, Query, File
from ninja.pagination import paginate
from ninja.files import UploadedFile
from ninja.errors import ValidationError
from django.db import IntegrityError
from django.utils.translation import gettext_lazy as _
from django.shortcuts import aget_object_or_404
from django.core.files.base import ContentFile
from typing import List, Optional
from asgiref.sync import sync_to_async
from mutagen.id3 import PictureType
from datetime import timedelta
import mutagen
import mimetypes

from users.api import AsyncHttpBearer
from helpers import make_errors, image_is_valid, is_audio_file

from schemas import TrackFull, TrackFilter, TrackSchemaIn
from tracks.models import Track
from albums.models import Album
from artists.models import Artist
from tracks.tags import read_tags


staff_auth = AsyncHttpBearer(is_staff=True)
router = Router(tags=['Tracks'], auth=staff_auth)


async def attach_image_to_model(image_info: dict, fname: str, instance: models.Model, instance_attr: str,  update: bool = False, save: bool = False):
    ext = mimetypes.guess_extension(image_info["mime"])
    fname = f"{fname}{ext}"
    upfile = UploadedFile(ContentFile(image_info["data"]), name=fname)

    if update:
        att = getattr(instance, instance_attr)
        await sync_to_async(att.save)(upfile.name, upfile, save=save)
    else:
        setattr(instance, instance_attr, upfile)


async def create_get_track_with_tags(tags, track, cache):
    # Check if track already exists in database
    try:
        track = await Track.objects.aget(
            title=tags["title"],
            genre=tags["genre"],
            year=tags["releaseYear"],
            number=tags["trackNumber"],
        )
        return track
    except Track.DoesNotExist:
        pass

    # Basic model without relationships
    track = Track(
        title=tags["title"],
        genre=tags["genre"],
        year=tags["releaseYear"],
        number=tags["trackNumber"],
        duration=tags["duration"],
        file=track,
    )

    # Attach album
    if tags.get('album'):
        album = await get_or_create_album(tags, cache)
        track.album = album

    # Otherwise treat track as single and check if there is a front cover image
    else:
        images = tags.get("images")
        for im in images:
            if im['type'] == PictureType.COVER_FRONT:
                await attach_image_to_model(im, tags['title'], track, 'cover')
                break

    await track.asave()
    if tags.get('artists'):
        aritsts = await get_or_create_artists(tags, cache)
        await track.artists.aadd(*aritsts)

    return track


async def get_or_create_album(tags, cache):
    album_name = tags.get("album")

    # Check if album has been fetched previously
    album = cache["albums"].get(album_name)
    if album:
        return album

    # If album artist is specified, issue stricter query
    if album_artist_name := tags.get('albumArtist'):
        # Check if artist has been fetched previously
        albumArtist = cache["artists"].get(album_artist_name)

        # Get or create album artist
        if not albumArtist:
            albumArtist, created = await Artist.objects.aget_or_create(
                name=album_artist_name)

        # If album artist does not have image, check if file has one
        if not albumArtist.image:
            image = None
            images = tags.get("images")
            for key, value in images.items():
                if value['type'] in [
                        PictureType.BAND_LOGOTYPE,
                        PictureType.LEAD_ARTIST, PictureType.ARTIST,
                        PictureType.BAND]:
                    image = images[key]
                    await attach_image_to_model(
                        image, albumArtist.name, albumArtist, 'image', True, True)
                    break

        cache['artists'][album_artist_name] = albumArtist
        album, created = await Album.objects.aget_or_create(
            name=album_name, artist=albumArtist)

        # Otherwise just use name
    else:
        album, created = await Album.objects.aget_or_create(
            name=album_name)

    # If album does not have cover image, check if file has one and attach it
    if not album.cover:
        images = tags.get("images")
        for im in images.values():
            if im['type'] in [
                PictureType.COVER_FRONT,
                PictureType.ILLUSTRATION,
                PictureType.MEDIA,
            ]:
                await attach_image_to_model(
                    im, album_name, album, 'cover', True, True)
                break

    # Put album in cache
    cache['albums'][album_name] = album
    return album


async def get_or_create_artists(tags, cache):
    artists = tags.get("artists")
    objs = []

    for aname in artists:
        artist = cache["artists"].get(aname)

        if not artist:
            artist, created = await Artist.objects.aget_or_create(name=aname)
            cache["artists"][aname] = artist
        objs.append(artist)
    return objs


@router.post('', response={201: TrackFull})
async def create_track(request, data: Form[TrackSchemaIn], file: UploadedFile = File(...), cover: UploadedFile = File(None)):
    # File metadata are ignored by this function, upload endpoint should be used instead
    errors = []
    clean_data = data.dict(exclude_unset=True)

    # Check if file is an actual audio file
    if not is_audio_file(file):
        raise ValidationError(
            [make_errors('file', _('File is not an audio file'))])

    dur = timedelta(seconds=mutagen.File(file.temporary_file_path()).info.length)

    artist_ids = [int(x) for x in clean_data.pop('artist_ids', []).split(',')]
    t = await Track.objects.acreate(duration=dur, file=file, **clean_data)

    # Check if album exists
    if album_id := clean_data.get('album_id'):
        if not await Album.objects.filter(pk=album_id).aexists():
            errors.append(make_errors('album_id', _('Album does not exist')))
    # Track is not part of any album, check if cover is valid image and attach it
    elif cover and image_is_valid(cover):
        t.cover = cover

    # Get as many aritists from database
    qs = Artist.objects.filter(pk__in=artist_ids)
    db_artists = await sync_to_async(list)(qs)

    # Attach artists to track
    await t.artists.aadd(*db_artists)
    return 201, await Track.objects.prefetch_related(
        'artists', 'album', 'album__artist').aget(pk=t.pk)



@router.post('/upload', response=List[TrackFull])
async def upload_tracks(request, tracks: List[UploadedFile] = File([])):
    cache = {
        'artists': {},
        'albums': {},
    }
    output = []
    music_files = [x for x in tracks if is_audio_file(x)]

    for track in music_files:
        fpath = track.temporary_file_path()
        file = mutagen.File(fpath)
        tags = read_tags(file, fpath)

        if tags:
            track = await create_get_track_with_tags(tags, track, cache)
            output.append(track.pk)
        else:
            track = await Track.objects.acreate(
                file=track, title='Unknown',
                duration=timedelta(seconds=file.info.length))
            output.append(track.pk)

    qs = Track.objects.prefetch_related(
        'artists', 'album', 'album__artist').filter(pk__in=output)
    return await sync_to_async(list)(qs)


@router.get('', response=List[TrackFull], auth=None)
@paginate
async def get_tracks(request, filters: Query[TrackFilter]):
    qs = Track.objects.prefetch_related('artists', 'album')
    return await sync_to_async(list)(filters.filter(qs))


@router.delete('/{int:trackID}', response={204: None})
async def delete_track(request, trackID: int):
    track = await aget_object_or_404(Track, pk=trackID)
    if track.cover:
        await sync_to_async(track.cover.delete)(save=False)
    await sync_to_async(track.file.delete)(save=False)
    await track.adelete()
    return 204, None
