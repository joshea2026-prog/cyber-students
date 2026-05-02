import json
from datetime import datetime, timezone
from .base import BaseHandler
from .crypto_utils import hash_token, decrypt_field

class AuthHandler(BaseHandler):

    def _decrypt_optional(self, ciphertext, iv):
        """Decrypt a field only if both ciphertext and IV are present."""
        if ciphertext is None or iv is None:
            return None
        return decrypt_field(ciphertext, iv)

    async def prepare(self):
        super(AuthHandler, self).prepare()
        if self.request.method == "OPTIONS":
            return

        token = None
        try:
            token = self.request.headers.get("X-Token")
            if not token:
                self.current_user = None
                self.send_error(400, message="You must provide a token!")
                return
        except Exception as e:
            print(f"Token extraction error: {e}")
            self.current_user = None
            self.send_error(400, message="You must provide a token!")
            return

        try:
            hashed_token = hash_token(token)
        except Exception as e:
            print(f"Token hashing error: {e}")
            self.current_user = None
            self.send_error(403, message="Token processing failed!")
            return

        try:
            user = await self.db.users.find_one(
                {"token": hashed_token},
                {
                    "email":           1,
                    "displayName":     1, "displayName_iv":    1,
                    "address":         1, "address_iv":        1,
                    "dateOfBirth":     1, "dateOfBirth_iv":    1,
                    "phoneNumber":     1, "phoneNumber_iv":    1,
                    "disabilities":    1, "disabilities_iv":   1,
                    "expiresIn":       1,
                }
            )
        except Exception as e:
            print(f"DB query error: {e}")
            self.current_user = None
            self.send_error(500, message="Database error!")
            return

        if user is None:
            self.current_user = None
            self.send_error(403, message="Your token is invalid!")
            return

        current_time = datetime.now(timezone.utc).timestamp()
        if current_time > user["expiresIn"]:
            self.current_user = None
            self.send_error(403, message="Your token has expired!")
            return

        try:
            display_name = decrypt_field(user["displayName"], user["displayName_iv"])
        except Exception:
            display_name = user["displayName"]

        # Decrypt optional fields — returns None if field was never stored
        address       = self._decrypt_optional(user.get("address"),      user.get("address_iv"))
        date_of_birth = self._decrypt_optional(user.get("dateOfBirth"),  user.get("dateOfBirth_iv"))
        phone_number  = self._decrypt_optional(user.get("phoneNumber"),  user.get("phoneNumber_iv"))

        # Deserialise disabilities list from JSON string after decryption
        disabilities_raw = self._decrypt_optional(user.get("disabilities"), user.get("disabilities_iv"))
        disabilities = json.loads(disabilities_raw) if disabilities_raw is not None else None

        self.current_user = {
            "email":        user["email"],
            "display_name": display_name,
            "address":      address,
            "date_of_birth": date_of_birth,
            "phone_number": phone_number,
            "disabilities": disabilities,
        }