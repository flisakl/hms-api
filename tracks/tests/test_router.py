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

    async def create_tracks(self):
        billy = await self.create_artist(name='Billy Joel')
        dawid = await self.create_artist(name='Dawid Bowie')
        skillet = await self.create_artist(name='Skillet')
        chs = await self.create_album('Cold Spring Harbor', artist=billy)
        hd = await self.create_album('Hunky Dory', artist=dawid)
        rise = await self.create_album('Rise', artist=skillet)
        dur = timedelta(minutes=1)
        f = ContentFile(b'', 'song.mp3')

        tracks = [
           Track(year=1971, genre='Pop', title='Tomorrow is today', album=chs, duration=dur, file=f),
           Track(year=1971, genre='Pop', title='Got to begin again', album=chs, duration=dur, file=f),
           Track(year=1973, genre='Rock', title='Changes', album=hd, duration=dur, file=f),
           Track(year=1973, genre='Rock', title='Eight line poem', album=hd, duration=dur, file=f),
           Track(year=2009, genre='Rock', title='Sick of it', album=rise, duration=dur, file=f),
        ]
        await Track.objects.abulk_create(tracks)
        await tracks[0].artists.aadd(billy)
        await tracks[1].artists.aadd(billy)
        await tracks[2].artists.aadd(dawid)
        await tracks[3].artists.aadd(dawid)
        await tracks[4].artists.aadd(skillet)

    async def test_tracks_can_be_filtered(self):
        with tempfile.TemporaryDirectory() as td, self.settings(MEDIA_ROOT=td):
            await self.create_tracks()

        response = await self.client.get('?title=Tomorrow')
        json = response.json()
        self.assertEqual(json['count'], 1)
        self.assertEqual(json['items'][0]['title'], 'Tomorrow is today')

        response = await self.client.get('?genre=rock')
        json = response.json()
        self.assertEqual(json['count'], 3)

        response = await self.client.get('?album=hunky')
        json = response.json()
        self.assertEqual(json['count'], 2)

        response = await self.client.get('?artist=skill')
        json = response.json()
        self.assertEqual(json['count'], 1)

        response = await self.client.get('?year_start=1970&year_end=1972')
        json = response.json()
        self.assertEqual(json['count'], 2)

        response = await self.client.get('?year_start=2000')
        json = response.json()
        self.assertEqual(json['count'], 1)
