from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import base64
import os
import keyring
import hashlib

def hash_password(passphrase: str) -> str:
    # Hash a password using Scrypt with a random salt.

    salt = os.urandom(16)                                    # unique random salt per password
    kdf = Scrypt(salt=salt, length=32, n=2**17, r=8, p=1)   # configure Scrypt KDF
    passphrase_bytes = bytes(passphrase, "utf-8")            # encode string to bytes for KDF
    hashed_passphrase = kdf.derive(passphrase_bytes)         # derive 32-byte hash
    return base64.b64encode(salt + hashed_passphrase).decode('utf-8')  # store salt + hash together


def verify_password(passphrase: str, stored_hash: str) -> bool:
    # Verify a plain-text password against a stored Scrypt hash.

    salt_hash_bytes = base64.b64decode(stored_hash.encode('utf-8'))  # decode from base64
    salt = salt_hash_bytes[:16]           # first 16 bytes are the salt
    expected_hash = salt_hash_bytes[16:]  # remaining bytes are the hash
    kdf = Scrypt(salt=salt, length=32, n=2**17, r=8, p=1)  # same params as hash_password
    passphrase_bytes = bytes(passphrase, "utf-8")
    computed_hash = kdf.derive(passphrase_bytes)    # re-derive hash from supplied password
    return computed_hash == expected_hash            # True only if hashes match


def hash_token(token: str) -> str:
    # Hash a session token using SHA-256 for DB storage

    digest = hashlib.sha256(token.encode('utf-8')).digest()  # produce 32-byte hash
    return base64.b64encode(digest).decode('utf-8')          # encode to base64 string

def _get_master_key() -> bytes:
    # Retrieve or generate the AES-256 master key from the system keyring.

    key_b64 = keyring.get_password('student_reg', 'aes256_key')
    if not key_b64:
        # First run — generate and persist a new random key
        key = os.urandom(32)
        keyring.set_password('student_reg', 'aes256_key', base64.b64encode(key).decode('utf-8'))
        return key
    # Subsequent runs — decode and return the stored key
    return base64.b64decode(key_b64.encode('utf-8'))


# Load the master key once at module import time so it is available to
# encrypt_field and decrypt_field without repeated keyring lookups.
MASTER_KEY = _get_master_key()


def encrypt_field(value: str) -> tuple[str, str]:
    # Encrypt a plain-text field value using AES-256-GCM.

    nonce = os.urandom(12)          # fresh cryptographically random 12-byte IV
    aesgcm = AESGCM(MASTER_KEY)     # initialise AES-GCM cipher with the master key
    ct = aesgcm.encrypt(nonce, value.encode('utf-8'), None)  # encrypt; None = no additional data
    ciphertext_b64 = base64.b64encode(ct).decode('utf-8')    # encode ciphertext for DB storage
    nonce_b64 = base64.b64encode(nonce).decode('utf-8')      # encode IV for DB storage
    return ciphertext_b64, nonce_b64


def decrypt_field(ciphertext_b64: str, nonce_b64: str) -> str:
    # Decrypt an AES-256-GCM encrypted field value.
    
    ct = base64.b64decode(ciphertext_b64.encode('utf-8'))    # decode ciphertext from base64
    nonce = base64.b64decode(nonce_b64.encode('utf-8'))      # decode IV from base64
    aesgcm = AESGCM(MASTER_KEY)                              # initialise cipher with master key
    pt = aesgcm.decrypt(nonce, ct, None)                     # decrypt and verify auth tag
    return pt.decode('utf-8')                                # return as plain-text string