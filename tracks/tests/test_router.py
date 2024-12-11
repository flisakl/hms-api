from django.core.files.uploadedfile import UploadedFile
from django.core.files.base import ContentFile
from django.utils.datastructures import MultiValueDict
from django.core.files import File
from ninja.testing import TestAsyncClient
from datetime import timedelta
from os import path
import tempfile

from helpers import TestHelper
from tracks.api import router
from tracks.models import Track


class TestAPI(TestHelper):
    def setUp(self):
        self.client = TestAsyncClient(router)

    async def test_only_staff_member_can_upload_tracks(self):
        user = await self.create_user()
        head = self.make_auth_header(user)

        response = await self.client.post('/upload', headers=head)

        self.assertEqual(response.status_code, 401)

    async def test_user_can_upload_music_files(self):
        member = await self.create_staff_member()
        head = self.make_auth_header(member)

        with tempfile.TemporaryDirectory() as td, self.settings(MEDIA_ROOT=td, FILE_UPLOAD_TEMP_DIR=td) as s, open(self.get_fp("song.mp3"), "rb") as f:
            files = MultiValueDict(
                {'tracks': [self.temp_file(File(f, 'song.mp3'), 'audio/mpeg', write=True)]}
            )
            response = await self.client.post('/upload', {}, FILES=files, headers=head)

        json = response.json()
        track = json[0]
        self.assertEqual(track["title"], "She's Got A Way")
        self.assertEqual(track["genre"], "Rock")
        self.assertEqual(track["year"], 1971)
        self.assertEqual(track["artists"][0]["name"], "Billy Joel")
        self.assertEqual(track["album"]["name"], "Cold Spring Harbor")
        self.assertNotEqual(track["album"]["cover"], None)
        self.assertEqual(track["artists"][0]["image"], None)
