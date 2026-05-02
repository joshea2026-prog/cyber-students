import json
from tornado.escape import json_decode

from .base import BaseHandler
from .crypto_utils import hash_password, encrypt_field
from .validators import parse_date

class RegistrationHandler(BaseHandler):

    def _encrypt_optional(self, value: str):
        """Encrypt a string value, returning (ciphertext, iv) or (None, None)."""
        if value is None:
            return None, None
        return encrypt_field(value)

    async def post(self):
        try:
            body = json_decode(self.request.body)
            email = body['email'].lower().strip()
            password = body['password']

            display_name = body.get('displayName')
            if display_name is None:
                display_name = email
            if not isinstance(display_name, str):
                raise Exception('Display name must be a string')

            # Optional fields — all default to None if not provided
            address      = body.get('address')
            date_of_birth = body.get('dateOfBirth')
            phone_number  = body.get('phoneNumber')
            disabilities  = body.get('disabilities')  # expected: list of strings

            # Validate types if provided
            if address is not None and not isinstance(address, str):
                raise Exception('Address must be a string')
            if phone_number is not None and not isinstance(phone_number, str):
                raise Exception('Phone number must be a string')
            if disabilities is not None and not isinstance(disabilities, list):
                raise Exception('Disabilities must be a list')

            # Validate and normalise date of birth if provided
            # parse_date accepts DD-MM-YYYY and DD/MM/YYYY, always returns DD-MM-YYYY
            if date_of_birth is not None:
                date_of_birth = parse_date(date_of_birth)

        except Exception:
            self.send_error(400, message='You must provide an email address, password and display name!')
            return

        if not email:
            self.send_error(400, message='The email address is invalid!')
            return

        if not password:
            self.send_error(400, message='The password is invalid!')
            return

        if not display_name:
            self.send_error(400, message='The display name is invalid!')
            return

        user = await self.db.users.find_one({'email': email})
        if user is not None:
            self.send_error(409, message='A user with the given email address already exists!')
            return

        # Encrypt displayName (always present)
        display_name_ct, display_name_iv = encrypt_field(display_name)

        # Encrypt optional fields — store None for both ciphertext and IV if absent
        address_ct,      address_iv      = self._encrypt_optional(address)
        dob_ct,          dob_iv          = self._encrypt_optional(date_of_birth)
        phone_ct,        phone_iv        = self._encrypt_optional(phone_number)

        # Serialise disabilities list to JSON string before encrypting
        disabilities_ct, disabilities_iv = self._encrypt_optional(
            json.dumps(disabilities) if disabilities is not None else None
        )

        await self.db.users.insert_one({
            'email':           email,
            'password':        hash_password(password),
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

        self.set_status(200)
        self.response['email']       = email
        self.response['displayName'] = display_name

        # Echo back optional fields only if they were provided
        if address is not None:
            self.response['address'] = address
        if date_of_birth is not None:
            self.response['dateOfBirth'] = date_of_birth   # already normalised to DD-MM-YYYY
        if phone_number is not None:
            self.response['phoneNumber'] = phone_number
        if disabilities is not None:
            self.response['disabilities'] = disabilities

        self.write_json()