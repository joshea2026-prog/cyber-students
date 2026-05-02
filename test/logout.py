import json
from json import dumps
from tornado.httputil import HTTPHeaders
from tornado.ioloop import IOLoop
from tornado.web import Application

from api.handlers.logout import LogoutHandler
from api.handlers.crypto_utils import hash_password, encrypt_field, hash_token

from .base import BaseTest


class LogoutHandlerTest(BaseTest):

    @classmethod
    def setUpClass(self):
        self.my_app = Application([(r'/logout', LogoutHandler)])
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

        self.email          = 'test@test.com'
        self.plain_password = 'testPassword'
        self.plain_token    = 'testToken'

        IOLoop.current().run_sync(self.register)
        IOLoop.current().run_sync(self.login)

    def test_logout(self):
        headers = HTTPHeaders({'X-Token': self.plain_token})
        body = {}

        response = self.fetch('/logout', headers=headers, method='POST', body=dumps(body))
        self.assertEqual(200, response.code)

    def test_logout_without_token(self):
        body = {}

        response = self.fetch('/logout', method='POST', body=dumps(body))
        self.assertEqual(400, response.code)

    def test_logout_wrong_token(self):
        headers = HTTPHeaders({'X-Token': 'wrongToken'})
        body = {}

        response = self.fetch('/logout', method='POST', body=dumps(body))
        self.assertEqual(400, response.code)

    def test_logout_twice(self):
        headers = HTTPHeaders({'X-Token': self.plain_token})
        body = {}

        response = self.fetch('/logout', headers=headers, method='POST', body=dumps(body))
        self.assertEqual(200, response.code)

        response_2 = self.fetch('/logout', headers=headers, method='POST', body=dumps(body))
        self.assertEqual(403, response_2.code)