import os
import magic
from PIL import Image
from django.utils.translation import gettext_lazy as _
from django.test import TestCase
from django.conf import settings
from django.core.files import File
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import TemporaryUploadedFile

from users.models import User
from artists.models import Artist
from albums.models import Album


def make_errors(field_name: str, msg):
    return {
        "loc": ["form", field_name],
        "msg": _(msg)
    }


def image_is_valid(image: TemporaryUploadedFile = None, buffer=None):
    if not image and image == buffer:
        raise ValueError('`image` or `buffer` must be provided')

    if image:
        path = image.temporary_file_path()
        # check content type
        if "image" not in image.content_type:
            return False

        # verify with Pillow
        try:
            with Image.open(path) as img:
                img.verify()
        except (IOError, SyntaxError):
            return False

        # check content with libmagic
        if "image" not in magic.Magic(mime=True).from_file(path):
            return False
    else:
        # check content with libmagic
        if "image" not in magic.Magic(mime=True).from_buffer(buffer):
            return False

    return True


def is_audio_file(audio_file: TemporaryUploadedFile):
    path = audio_file.temporary_file_path()
    # check content type
    if "audio" not in audio_file.content_type:
        return False

    # check content with libmagic
    if "audio" not in magic.Magic(mime=True).from_file(path):
        return False

    return True


class TestHelper(TestCase):
    DATA_DIR = settings.BASE_DIR / 'test_data/'

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
        return await self.create_user(staff=True, **kwargs)

    async def create_artist(self, name='Billy Joel'):
        return await Artist.objects.acreate(name=name)

    async def create_album(self, name: str, artist: Artist = None):
        if not artist:
            artist = await self.create_artist()
        album = Album(name=name, artist=artist)
        await album.asave()
        return album

    def make_auth_header(self, user: User):
        return {
            'Authorization': f'Bearer {user.token}'
        }

    # Helpers for handling files
    def get_fp(self, filename: str):
        return os.path.join(self.DATA_DIR,  filename)

    def temp_file(self, file: File, ctype: str = 'image/jpeg', write: bool = False):
        tf = TemporaryUploadedFile(
            name=file.name,
            content_type=ctype,
            size=file.size,
            charset='utf-8'
        )

        if write:
            tf.file.write(file.read())
        return tf

    def content_file(self, data: bytes, name: str):
        return ContentFile(data, name)

    def fileExists(self, location, filename: str):
        path = os.path.join(location, filename)
        return os.path.isfile(path)
