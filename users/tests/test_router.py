from helpers import TestHelper
from ninja.testing import TestAsyncClient

from users.api import router


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
