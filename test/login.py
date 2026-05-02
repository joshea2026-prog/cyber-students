import json
from json import dumps
from tornado.escape import json_decode
from tornado.ioloop import IOLoop
from tornado.web import Application

from .base import BaseTest

from api.handlers.login import LoginHandler
from api.handlers.crypto_utils import hash_password, encrypt_field


class LoginHandlerTest(BaseTest):

    @classmethod
    def setUpClass(self):
        self.my_app = Application([(r'/login', LoginHandler)])
        super().setUpClass()

    async def register(self):
        display_name_ct, display_name_iv = encrypt_field('testDisplayName')
        address_ct,      address_iv      = encrypt_field('123 Test Street, Cork')
        dob_ct,          dob_iv          = encrypt_field('01-01-1990')
        phone_ct,        phone_iv        = encrypt_field('+353871234567')
        disabilities_ct, disabilities_iv = encrypt_field(json.dumps(['dyslexia', 'ADHD']))

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

    def setUp(self):
        super().setUp()

        self.email        = 'test@test.com'
        self.plain_password = 'testPassword'

        IOLoop.current().run_sync(self.register)

    def test_login(self):
        body = {
            'email':    self.email,
            'password': self.plain_password
        }

        response = self.fetch('/login', method='POST', body=dumps(body))
        self.assertEqual(200, response.code)

        body_2 = json_decode(response.body)
        self.assertIsNotNone(body_2['token'])
        self.assertIsNotNone(body_2['expiresIn'])

    def test_login_case_insensitive(self):
        body = {
            'email':    self.email.swapcase(),
            'password': self.plain_password
        }

        response = self.fetch('/login', method='POST', body=dumps(body))
        self.assertEqual(200, response.code)

        body_2 = json_decode(response.body)
        self.assertIsNotNone(body_2['token'])
        self.assertIsNotNone(body_2['expiresIn'])

    def test_login_wrong_email(self):
        body = {
            'email':    'wrongUsername',
            'password': self.plain_password
        }

        response = self.fetch('/login', method='POST', body=dumps(body))
        self.assertEqual(403, response.code)

    def test_login_wrong_password(self):
        body = {
            'email':    self.email,
            'password': 'wrongPassword'
        }

        response = self.fetch('/login', method='POST', body=dumps(body))
        self.assertEqual(403, response.code)