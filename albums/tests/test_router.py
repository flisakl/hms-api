import tempfile
from ninja.testing import TestAsyncClient
from django.core.files import File

from helpers import TestHelper

from albums.api import router
from artists.models import Artist


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
            data = {'name': 'Cold Spring Harbor', 'artist_id': artist.pk, 'genre': 'Pop'}
            file = {'cover': self.temp_file(File(f, 'image.jpg'), write=True)}
            response = await self.client.post('', data, FILES=file, headers=head)

            expected = {
                'id': 1,
                'name': 'Cold Spring Harbor',
                'cover': '/media/albums/image.jpg',
                'genre': 'Pop',
                'year': None,
                'artist': {
                    'id': 1,
                    'name': 'Billy Joel',
                    'image': None
                }
            }
            self.assertEqual(response.status_code, 201)
            self.assertJSONEqual(response.content, expected)
