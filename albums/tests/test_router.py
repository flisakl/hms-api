import tempfile
from datetime import timedelta
from ninja.testing import TestAsyncClient
from django.core.files import File

from helpers import TestHelper

from albums.api import router
from albums.models import Album
from tracks.models import Track


class TestRouter(TestHelper):
    def setUp(self):
        self.client = TestAsyncClient(router)

    async def test_regular_user_can_not_add_album(self):
        user = await self.create_user()
        head = self.make_auth_header(user)

        response = await self.client.post('', headers=head)

        self.assertEqual(response.status_code, 401)

    async def test_staff_member_can_add_album(self):
        member = await self.create_staff_member()
        head = {'Authorization': f"Bearer {member.token}"}

        with tempfile.TemporaryDirectory() as td, self.settings(MEDIA_ROOT=td, FILE_UPLOAD_TEMP_DIR=td) as s, open(self.get_fp("image.jpg"), "rb") as f:
            artist = await self.create_artist()
            data = {'name': 'Cold Spring Harbor',
                    'artist_id': artist.pk, 'genre': 'Pop'}
            file = {'cover': self.temp_file(File(f, 'image.jpg'), write=True)}
            response = await self.client.post('', data, FILES=file, headers=head)

            expected = {
                'id': 1,
                'name': 'Cold Spring Harbor',
                'cover': '/media/albums/image.jpg',
                'genre': 'Pop',
                'year': None,
                'track_count': 0,
                'artist': {
                    'id': 1,
                    'name': 'Billy Joel',
                    'image': None
                }
            }
            self.assertEqual(response.status_code, 201)
            self.assertJSONEqual(response.content, expected)

    async def test_guest_can_filter_albums_by_name(self):
        artist = await self.create_artist()
        albums = [
            Album(name='Cold Spring Harbor', artist=artist),
            Album(name='Atilla', artist=artist),
        ]
        await Album.objects.abulk_create(albums)

        response = await self.client.get('?name=cold')

        expected = {
            'items': [
                {
                    'id': 1,
                    'name': albums[0].name,
                    'cover': None,
                    'year': None,
                    'genre': None,
                    'artist': {
                        'id': 1,
                        'name': artist.name,
                        'image': None,
                    },
                    'track_count': 0,
                }
            ],
            'count': 1,
        }
        self.assertJSONEqual(response.content, expected)

    async def test_guest_can_get_album_details(self):
        artist = await self.create_artist()
        album = await Album.objects.acreate(
            name='Cold Spring Harbor', artist=artist)
        with tempfile.TemporaryDirectory() as td, self.settings(MEDIA_ROOT=td, FILE_UPLOAD_TEMP_DIR=td) as s, open(self.get_fp("image.jpg"), "rb") as f:

            f = self.temp_file(File(f, 'song.mp3'), write=True)
            await Track.objects.acreate(
                file=f, title='Why Judy Why',
                duration=timedelta(seconds=200),
                genre='Rock', album=album
            )

        response = await self.client.get(f"/{album.pk}")
        json = response.json()

        self.assertEqual(json['name'], 'Cold Spring Harbor')
        self.assertEqual(json['artist']['name'], 'Billy Joel')
        self.assertEqual(json['tracks'][0]['title'], 'Why Judy Why')

    async def test_regular_user_can_not_update_album(self):
        user = await self.create_user()
        head = self.make_auth_header(user)
        artist2 = await self.create_artist(name='Johnny Cash')
        album = await Album.objects.acreate(name='CHS', artist=artist2)

        response = await self.client.put(f"/{album.pk}", headers=head)

        self.assertEqual(response.status_code, 401)

    async def test_staff_member_can_update_album(self):
        member = await self.create_staff_member()
        head = self.make_auth_header(member)
        artist = await self.create_artist()
        artist2 = await self.create_artist(name='Johnny Cash')
        album = await Album.objects.acreate(name='CHS', artist=artist2)

        with tempfile.TemporaryDirectory() as td, self.settings(MEDIA_ROOT=td, FILE_UPLOAD_TEMP_DIR=td) as s, open(self.get_fp("image.jpg"), "rb") as f:
            data = {'name': 'Cold Spring Harbor', 'artist_id': artist.pk, 'year': 1971, 'genre': 'Rock'}
            file = {'cover': self.temp_file(File(f, 'image.jpg'), write=True)}
            response = await self.client.put(
                f"/{album.pk}", data, FILES=file, headers=head)

            expected = {
                'id': 1,
                'name': 'Cold Spring Harbor',
                'cover': '/media/albums/image.jpg',
                'year': 1971,
                'genre': 'Rock',
                'artist': {
                    'id': 1,
                    'name': 'Billy Joel',
                    'image': None
                }
            }
            self.assertEqual(response.status_code, 200)
            self.assertJSONEqual(response.content, expected)

    async def test_regular_user_can_not_delete_album(self):
        user = await self.create_user()
        head = {'Authorization': f"Bearer {user.token}"}
        artist2 = await self.create_artist(name='Johnny Cash')
        album = await Album.objects.acreate(name='CHS', artist=artist2)

        response = await self.client.delete(f"/{album.pk}", headers=head)

        self.assertEqual(response.status_code, 401)

    async def test_staff_member_can_delete_album(self):
        member = await self.create_staff_member()
        head = {'Authorization': f"Bearer {member.token}"}
        artist2 = await self.create_artist(name='Johnny Cash')

        with tempfile.TemporaryDirectory() as td, self.settings(MEDIA_ROOT=td, FILE_UPLOAD_TEMP_DIR=td) as s, open(self.get_fp("image.jpg"), "rb") as f:
            file = self.temp_file(File(f, 'image.jpg'), write=True)
            album = await Album.objects.acreate(
                name='CHS', artist=artist2, cover=file)

            self.assertTrue(self.fileExists(td, 'albums/image.jpg'))

            response = await self.client.delete(
                f"/{album.pk}", headers=head)
            response2 = await self.client.delete(
                f"/{album.pk}", headers=head)

            self.assertFalse(self.fileExists(td, 'albums/image.jpg'))
            self.assertEqual(response.status_code, 204)
            self.assertEqual(response2.status_code, 404)
