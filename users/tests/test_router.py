import tempfile
from django.core.files import File
from helpers import TestHelper
from ninja.testing import TestAsyncClient

from users.api import router
from users.models import User


class TestCreate(TestHelper):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.data = {
            'first_name': 'Jane',
            'username': 'Jane99',
            'email': 'jane@example.com',
            'password1': 'Test1234',
            'password2': 'Test1234'
        }

    def setUp(self):
        self.client = TestAsyncClient(router)

    async def test_guest_can_create_account(self):
        data = self.data.copy()
        data['is_superuser'] = True  # Check if additional data are discarded
        response = await self.client.post('', data)
        json = response.json()

        self.assertEqual(response.status_code, 201)
        self.assertEqual(json['first_name'], 'Jane')
        self.assertFalse(json['is_superuser'])

    async def test_email_address_must_be_unique(self):
        data = self.data.copy()
        user = await self.create_user()
        data['email'] = user.email

        response = await self.client.post('', data)
        json = response.json()['detail']

        self.assertEqual(response.status_code, 422)
        self.assertEqual(len(json), 1)
        self.assertIn('email', json[0]['loc'])

    async def test_username_must_be_unique(self):
        data = self.data.copy()
        user = await self.create_user()
        data['username'] = user.username

        response = await self.client.post('', data)
        json = response.json()['detail']

        self.assertEqual(response.status_code, 422)
        self.assertEqual(len(json), 1)
        self.assertIn('username', json[0]['loc'])


class TestRead(TestHelper):
    def setUp(self):
        self.sclient = self.client
        self.client = TestAsyncClient(router)

    async def test_only_superuser_can_retrieve_user_list(self):
        super = await self.create_user(superuser=True)
        normie = await self.create_user(username='Mike')
        await self.create_user(username='Johnny')
        path = '?username=jo'

        response = await self.client.get(path, headers=self.make_auth_header(super))
        response2 = await self.client.get(path, headers=self.make_auth_header(normie))
        json = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response2.status_code, 401)
        self.assertEqual(len(json), 2)

    async def test_only_superuser_can_retrieve_user(self):
        super = await self.create_user(superuser=True)
        normie = await self.create_user(username='Mike')
        await self.create_user(username='Johnny')
        path = f'{super.pk}'

        response = await self.client.get(path, headers=self.make_auth_header(super))
        response2 = await self.client.get(path, headers=self.make_auth_header(normie))
        json = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response2.status_code, 401)
        self.assertEqual(json['username'], super.username)


class TestUpdate(TestHelper):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.data = {
            'first_name': 'Jane',
            'username': 'Jane99',
            'email': 'jane@example.com',
            'password1': 'Test1234',
            'password2': 'Test1234'
        }

    def setUp(self):
        self.client = TestAsyncClient(router)

    async def test_user_can_change_name_and_avatar(self):
        with tempfile.TemporaryDirectory() as td, self.settings(MEDIA_ROOT=td, FILE_UPLOAD_TEMP_DIR=td) as s, open(self.get_fp("image.jpg"), "rb") as f:
            img_to_upload = self.temp_file(File(f, "avatar.jpg"), write=True)
            old_avatar = self.content_file(b"", "test.jpg")
            user = await self.create_user(image=old_avatar)
            data = {'first_name': 'Mary', 'last_name': 'Thomson'}

            self.assertTrue(self.fileExists(td, f"avatars/{old_avatar.name}"))
            response = await self.client.patch(
                '',
                data,
                headers=self.make_auth_header(user),
                FILES={'avatar': img_to_upload})

            self.assertEqual(response.status_code, 200)
            self.assertTrue(self.fileExists(
                td, f"avatars/{img_to_upload.name}"))

    async def test_user_must_provide_valid_image(self):
        with tempfile.TemporaryDirectory() as td, self.settings(MEDIA_ROOT=td, FILE_UPLOAD_TEMP_DIR=td) as s, open(self.get_fp("image.jpg"), "rb") as f:
            image = File(f, "image.jpg")
            av = self.temp_file(self.content_file(b"", "junk.pdf"))
            user = await self.create_user(image=image)
            data = {'first_name': 'Mark', 'last_name': 'Twain'}

            response = await self.client.patch(
                '', data, headers=self.make_auth_header(user),
                FILES={'avatar': av}
            )

            # Old avatar is not replaced by invalid file
            self.assertEqual(response.status_code, 422)
            self.assertFalse(self.fileExists(td, av.name))
            self.assertTrue(self.fileExists(td, f"avatars/{image.name}"))


class TestDelete(TestHelper):

    def setUp(self):
        self.client = TestAsyncClient(router)

    async def test_user_can_delete_his_account(self):
        with tempfile.TemporaryDirectory() as td, self.settings(MEDIA_ROOT=td, FILE_UPLOAD_TEMP_DIR=td) as s:
            av = self.temp_file(self.content_file(b"", "junk.pdf"))
            user = await self.create_user(image=av)

            self.assertTrue(self.fileExists(td, f'avatars/{av.name}'))

            response = await self.client.delete(
                '', headers=self.make_auth_header(user)
            )

            self.assertEqual(response.status_code, 204)
            # Avatar has been deleted
            self.assertFalse(self.fileExists(td, f'avatars/{av.name}'))
            # User no longer exists in database
            with self.assertRaises(User.DoesNotExist):
                await User.objects.aget(pk=user.pk)


class TestMisc(TestHelper):
    def setUp(self):
        self.client = TestAsyncClient(router)

    async def test_user_can_change_his_password(self):
        passwd = 'Test1234'
        newpass = 'NewCoolPassword1'
        user = await self.create_user(password=passwd)
        data = {
            'old_password': passwd,
            'password1': newpass, 'password2': newpass,
        }
        headers = self.make_auth_header(user)

        url = 'password-change'
        response = await self.client.post(url, data, headers=headers)

        await user.arefresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(user.check_password(newpass))

    async def test_superuser_can_change_user_role(self):
        user = await self.create_user(superuser=True)
        normie = await self.create_user(username="Frank")
        data = {
            'is_superuser': True,
            'is_staff': True,
        }
        headers = self.make_auth_header(user)
        headers2 = self.make_auth_header(normie)

        url = f'/{normie.pk}'
        # Performed by normie
        response2 = await self.client.post(url, data, headers=headers2)
        # Performed by superuser
        response = await self.client.post(url, data, headers=headers)
        js = response.json()

        await normie.arefresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(True, js['is_superuser'] == js['is_staff'])
        self.assertEqual(response2.status_code, 401)

    async def test_guest_can_log_in(self):
        upass = 'Test1234'
        user = await self.create_user(superuser=True, password=upass)
        data = {
            'username': user.email,
            'password': upass
        }

        url = '/login'
        response = await self.client.post(url, data)
        js = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(js['username'], user.username)
