from pwdlib import PasswordHash


class PasswordHelper:
    """Hash and verify passwords; password hashes cannot be decrypted."""

    def __init__(self):
        self._hasher = PasswordHash.recommended()
        self._dummy_hash = self._hasher.hash("not-a-real-password")

    def hash(self, password: str) -> str:
        """Hash a password with the configured password hasher."""
        return self._hasher.hash(password)

    def verify(self, password: str, password_hash: str | None) -> bool:
        """Verify a password against a hash, including the dummy hash for missing users."""
        return self._hasher.verify(password, password_hash or self._dummy_hash)


password_helper = PasswordHelper()
