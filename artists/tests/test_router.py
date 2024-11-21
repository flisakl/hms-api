import tempfile
from ninja.testing import TestAsyncClient
from django.core.files import File

from helpers import TestHelper

from artists.api import router


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
