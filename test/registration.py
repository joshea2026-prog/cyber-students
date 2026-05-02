from json import dumps
from tornado.escape import json_decode
from tornado.web import Application

from api.handlers.registration import RegistrationHandler

from .base import BaseTest


class RegistrationHandlerTest(BaseTest):

    @classmethod
    def setUpClass(self):
        self.my_app = Application([(r'/registration', RegistrationHandler)])
        super().setUpClass()

    def test_registration(self):
        email = 'test@test.com'
        display_name = 'testDisplayName'

        body = {
            'email':       email,
            'password':    'testPassword',
            'displayName': display_name
        }

        response = self.fetch('/registration', method='POST', body=dumps(body))
        self.assertEqual(200, response.code)

        body_2 = json_decode(response.body)
        self.assertEqual(email, body_2['email'])
        self.assertEqual(display_name, body_2['displayName'])

    def test_registration_without_display_name(self):
        email = 'test@test.com'

        body = {
            'email':    email,
            'password': 'testPassword'
        }

        response = self.fetch('/registration', method='POST', body=dumps(body))
        self.assertEqual(200, response.code)

        body_2 = json_decode(response.body)
        self.assertEqual(email, body_2['email'])
        self.assertEqual(email, body_2['displayName'])

    def test_registration_with_all_optional_fields(self):
        email = 'test@test.com'
        display_name = 'testDisplayName'
        address = '123 Test Street, Cork'
        phone_number = '+353871234567'
        disabilities = ['dyslexia', 'ADHD']

        body = {
            'email':        email,
            'password':     'testPassword',
            'displayName':  display_name,
            'address':      address,
            'dateOfBirth':  '01-01-1990',
            'phoneNumber':  phone_number,
            'disabilities': disabilities
        }

        response = self.fetch('/registration', method='POST', body=dumps(body))
        self.assertEqual(200, response.code)

        body_2 = json_decode(response.body)
        self.assertEqual(email,         body_2['email'])
        self.assertEqual(display_name,  body_2['displayName'])
        self.assertEqual(address,        body_2['address'])
        self.assertEqual('01-01-1990',  body_2['dateOfBirth'])
        self.assertEqual(phone_number,  body_2['phoneNumber'])
        self.assertEqual(disabilities,  body_2['disabilities'])

    def test_registration_with_some_optional_fields(self):
        """Partial optional fields — only provided ones appear in response."""
        email = 'test@test.com'

        body = {
            'email':       email,
            'password':    'testPassword',
            'phoneNumber': '+353871234567'
        }

        response = self.fetch('/registration', method='POST', body=dumps(body))
        self.assertEqual(200, response.code)

        body_2 = json_decode(response.body)
        self.assertEqual(email, body_2['email'])
        self.assertEqual('+353871234567', body_2['phoneNumber'])
        # Unprovided optional fields must not appear in the response
        self.assertNotIn('address',      body_2)
        self.assertNotIn('dateOfBirth',  body_2)
        self.assertNotIn('disabilities', body_2)

    def test_registration_twice(self):
        body = {
            'email':       'test@test.com',
            'password':    'testPassword',
            'displayName': 'testDisplayName'
        }

        response = self.fetch('/registration', method='POST', body=dumps(body))
        self.assertEqual(200, response.code)

        response_2 = self.fetch('/registration', method='POST', body=dumps(body))
        self.assertEqual(409, response_2.code)

 
    # --- Date of birth validation tests ---
 
    def test_registration_date_dash_format(self):
        """DD-MM-YYYY format is accepted and returned as-is."""
        body = {
            'email':       'test@test.com',
            'password':    'testPassword',
            'dateOfBirth': '15-06-1995'
        }
 
        response = self.fetch('/registration', method='POST', body=dumps(body))
        self.assertEqual(200, response.code)
 
        body_2 = json_decode(response.body)
        self.assertEqual('15-06-1995', body_2['dateOfBirth'])
 
    def test_registration_date_slash_format(self):
        """DD/MM/YYYY format is accepted and normalised to DD-MM-YYYY."""
        body = {
            'email':       'test@test.com',
            'password':    'testPassword',
            'dateOfBirth': '15/06/1995'
        }
 
        response = self.fetch('/registration', method='POST', body=dumps(body))
        self.assertEqual(200, response.code)
 
        body_2 = json_decode(response.body)
        # Slash input normalised to dash format on storage and response
        self.assertEqual('15-06-1995', body_2['dateOfBirth'])
 
    def test_registration_date_iso_format_rejected(self):
        """ISO format YYYY-MM-DD is not a valid Irish date format."""
        body = {
            'email':       'test@test.com',
            'password':    'testPassword',
            'dateOfBirth': '1995-06-15'
        }
 
        response = self.fetch('/registration', method='POST', body=dumps(body))
        self.assertEqual(400, response.code)
 
    def test_registration_date_invalid_day(self):
        """A date with an impossible day is rejected."""
        body = {
            'email':       'test@test.com',
            'password':    'testPassword',
            'dateOfBirth': '32-01-1990'
        }
 
        response = self.fetch('/registration', method='POST', body=dumps(body))
        self.assertEqual(400, response.code)
 
    def test_registration_date_invalid_leap_year(self):
        """29th February on a non-leap year is rejected."""
        body = {
            'email':       'test@test.com',
            'password':    'testPassword',
            'dateOfBirth': '29-02-1991'
        }
 
        response = self.fetch('/registration', method='POST', body=dumps(body))
        self.assertEqual(400, response.code)
 
    def test_registration_date_valid_leap_year(self):
        """29th February on a valid leap year is accepted."""
        body = {
            'email':       'test@test.com',
            'password':    'testPassword',
            'dateOfBirth': '29-02-1992'
        }
 
        response = self.fetch('/registration', method='POST', body=dumps(body))
        self.assertEqual(200, response.code)
 
        body_2 = json_decode(response.body)
        self.assertEqual('29-02-1992', body_2['dateOfBirth'])

