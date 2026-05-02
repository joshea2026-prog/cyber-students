import json
from json import dumps
from tornado.escape import json_decode
from tornado.httputil import HTTPHeaders
from tornado.ioloop import IOLoop
from tornado.web import Application

from api.handlers.user import UserHandler
from api.handlers.crypto_utils import hash_password, encrypt_field, hash_token

from .base import BaseTest


class UserHandlerTest(BaseTest):

    @classmethod
    def setUpClass(self):
        self.my_app = Application([(r'/user', UserHandler)])
        super().setUpClass()

    async def register(self):
        display_name_ct, display_name_iv = encrypt_field(self.plain_display_name)
        address_ct,      address_iv      = encrypt_field(self.plain_address)
        dob_ct,          dob_iv          = encrypt_field(self.plain_date_of_birth)
        phone_ct,        phone_iv        = encrypt_field(self.plain_phone_number)
        # Serialise disabilities list to JSON string before encrypting
        disabilities_ct, disabilities_iv = encrypt_field(json.dumps(self.plain_disabilities))

        await self.get_app().db.users.insert_one({
            'email':           self.email,
            'password':        hash_password(self.plain_password),
            'displayName':     display_name_ct,
            'displayName_iv':  display_name_iv,
            'address':         address_ct,
            'address_iv':      address_iv,
            'dateOfBirth':     dob_ct,
            'dateOfBirth_iv':  dob_iv,
            'phoneNumber':     phone_ct,
            'phoneNumber_iv':  phone_iv,
            'disabilities':    disabilities_ct,
            'disabilities_iv': disabilities_iv,
        })

    async def login(self):
        await self.get_app().db.users.update_one({
            'email': self.email
        }, {
            '$set': {
                'token':     hash_token(self.plain_token),
                'expiresIn': 2147483647
            }
        })

    def setUp(self):
        super().setUp()

        self.email              = 'test@test.com'
        self.plain_password     = 'testPassword'
        self.plain_display_name = 'testDisplayName'
        self.plain_token        = 'testToken'
        self.plain_address      = '123 Test Street, Cork'
        self.plain_date_of_birth = '01-01-1990'
        self.plain_phone_number = '+353871234567'
        self.plain_disabilities = ['dyslexia', 'ADHD']

        IOLoop.current().run_sync(self.register)
        IOLoop.current().run_sync(self.login)

    def test_user(self):
        headers = HTTPHeaders({'X-Token': self.plain_token})

        response = self.fetch('/user', headers=headers)
        self.assertEqual(200, response.code)

        body_2 = json_decode(response.body)
        # Email is plain text in DB and in response
        self.assertEqual(self.email,               body_2['email'])
        # All fields are decrypted by auth.py before the handler responds
        self.assertEqual(self.plain_display_name,  body_2['displayName'])
        self.assertEqual(self.plain_address,        body_2['address'])
        self.assertEqual(self.plain_date_of_birth,  body_2['dateOfBirth'])
        self.assertEqual(self.plain_phone_number,   body_2['phoneNumber'])
        self.assertEqual(self.plain_disabilities,   body_2['disabilities'])

    def test_user_without_token(self):
        response = self.fetch('/user')
        self.assertEqual(400, response.code)

    def test_user_wrong_token(self):
        headers = HTTPHeaders({'X-Token': 'wrongToken'})

        response = self.fetch('/user')
        self.assertEqual(400, response.code)