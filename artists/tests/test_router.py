import tempfile
from ninja.testing import TestAsyncClient
from django.core.files import File

from helpers import TestHelper

from artists.api import router
from artists.models import Artist


class TestRouter(TestHelper):
    def setUp(self):
        self.client = TestAsyncClient(router)

    async def test_staff_member_can_add_artist(self):
        member = await self.create_staff_member()
        normie = await self.create_user(username='jack')
        head = self.make_auth_header(member)
        head2 = self.make_auth_header(normie)

        with tempfile.TemporaryDirectory() as td, self.settings(MEDIA_ROOT=td, FILE_UPLOAD_TEMP_DIR=td) as s, open(self.get_fp("image.jpg"), "rb") as f:
            data = {'name': 'Billy Joel'}
            file = {'image': self.temp_file(File(f, 'image.jpg'), write=True)}
            res = await self.client.post('', data, FILES=file, headers=head)
            res2 = await self.client.post('', data, FILES=file, headers=head2)

            expected = {
                'id': 1,
                'name': 'Billy Joel',
                'image': '/media/artists/image.jpg'
            }
            self.assertEqual(res.status_code, 201)
            self.assertEqual(res2.status_code, 401)
            self.assertJSONEqual(res.content, expected)

    async def test_guest_user_can_filter_artists_by_name(self):
        artists = [
            Artist(name='Bob Marley'), Artist(name='Johnny Cash'),
            Artist(name='Bob Dylan'), Artist(name='Billy Joel'),
        ]
        await Artist.objects.abulk_create(artists)

        response = await self.client.get('?name=bob')
        json = response.json()

        self.assertEqual(json['count'], 2)
        self.assertIn('Bob', json['items'][0]['name'])
        self.assertIn('Bob', json['items'][1]['name'])

    async def test_guest_user_can_access_artist_data(self):
        artist = await Artist.objects.acreate(name='Dawid Bowie')
        # TODO uncomment the code once Album model is defined
        # await Album.objects.acreate(name='The Man Who Sold The World',
        #                             artist=artist)

        response = await self.client.get(f"/{artist.pk}")

        expected = {
            'id': 1,
            'name': 'Dawid Bowie',
            'image': None,
            # 'albums': [
            #     {
            #         'id': 1,
            #         'name': 'The Man Who Sold The World',
            #         'cover': None
            #     }
            # ]
        }
        self.assertJSONEqual(response.content, expected)

    async def test_regular_user_can_not_update_artist(self):
        user = await self.create_user()
        data = {'name': 'Billy Joel'}
        head = self.make_auth_header(user)
        artist = await Artist.objects.acreate(name='Test')

        response = await self.client.put(f"/{artist.pk}", data, headers=head)

        self.assertEqual(response.status_code, 401)

    async def test_staff_member_can_update_artist(self):
        with tempfile.TemporaryDirectory() as td, self.settings(MEDIA_ROOT=td, FILE_UPLOAD_TEMP_DIR=td) as s, open(self.get_fp("image.jpg"), "rb") as f:
            data = {'name': 'Billy Joel'}
            img_to_upload = self.temp_file(File(f, "avatar.jpg"), write=True)
            old_avatar = self.content_file(b"", "test.jpg")
            member = await self.create_staff_member()
            head = self.make_auth_header(member)

            artist = await Artist.objects.acreate(
                name='Billy Joelio', image=old_avatar)
            response = await self.client.put(
                f"/{artist.pk}", data, FILES={'image': img_to_upload},
                headers=head)
            json = response.json()

            self.assertFalse(self.fileExists(td, f"artists/{old_avatar.name}"))
            self.assertEqual(response.status_code, 200)
            self.assertEqual(json['name'], 'Billy Joel')
            self.assertTrue(self.fileExists(td, f"artists/{img_to_upload.name}"))

    async def test_staff_member_can_add_artist_with_put_request(self):
        with tempfile.TemporaryDirectory() as td, self.settings(MEDIA_ROOT=td, FILE_UPLOAD_TEMP_DIR=td) as s, open(self.get_fp("image.jpg"), "rb") as f:
            data = {'name': 'Billy Joel'}
            img_to_upload = self.temp_file(File(f, "avatar.jpg"), write=True)
            member = await self.create_staff_member()
            head = self.make_auth_header(member)

            response = await self.client.put(
                "/1", data, FILES={'image': img_to_upload},
                headers=head)
            json = response.json()

            self.assertTrue(self.fileExists(td, f"artists/{img_to_upload.name}"))
            self.assertEqual(response.status_code, 200)
            self.assertEqual(json['name'], 'Billy Joel')

    async def test_regular_user_can_not_delete_artist(self):
        user = await self.create_user()
        data = {'name': 'Billy Joel'}
        head = {'Authorization': f"Bearer {user.token}"}
        artist = await Artist.objects.acreate(name='Test')
        url = f"/{artist.pk}"

        response = await self.client.delete(url, data, headers=head)

        self.assertEqual(response.status_code, 401)

    async def test_staff_member_can_delete_artist(self):
        with tempfile.TemporaryDirectory() as td, self.settings(MEDIA_ROOT=td, FILE_UPLOAD_TEMP_DIR=td) as s:
            old_avatar = self.content_file(b"", "test.jpg")
            member = await self.create_staff_member()
            head = self.make_auth_header(member)

            artist = await Artist.objects.acreate(
                name='Billy Joelio', image=old_avatar)

            url = f"/{artist.pk}"
            self.assertTrue(self.fileExists(td, 'artists/test.jpg'))
            response = await self.client.delete(url, headers=head)
            response2 = await self.client.delete(url, headers=head)

            self.assertEqual(response.status_code, 204)
            self.assertEqual(response2.status_code, 404)
            self.assertFalse(self.fileExists(td, 'artists/test.jpg'))
            with self.assertRaises(Artist.DoesNotExist):
                await Artist.objects.aget(pk=artist.pk)
