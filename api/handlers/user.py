from tornado.web import authenticated

from .auth import AuthHandler
from .crypto_utils import decrypt_field

class UserHandler(AuthHandler):

    @authenticated
    def get(self):
        self.set_status(200)
        self.response['email']       = self.current_user['email']
        self.response['displayName'] = self.current_user['display_name']

        # Include optional fields in response only if they were stored
        if self.current_user.get('address') is not None:
            self.response['address'] = self.current_user['address']
        if self.current_user.get('date_of_birth') is not None:
            self.response['dateOfBirth'] = self.current_user['date_of_birth']
        if self.current_user.get('phone_number') is not None:
            self.response['phoneNumber'] = self.current_user['phone_number']
        if self.current_user.get('disabilities') is not None:
            self.response['disabilities'] = self.current_user['disabilities']

        self.write_json()