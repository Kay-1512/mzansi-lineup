from django.contrib.auth.hashers import check_password, make_password
from django.test import override_settings

from apps.core.hashers import OwaspPBKDF2PasswordHasher

HASHERS = [
    "apps.core.hashers.OwaspPBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
]


class TestOwaspPBKDF2PasswordHasher:
    def test_uses_600_000_iterations_not_djangos_1_000_000_default(self):
        assert OwaspPBKDF2PasswordHasher.iterations == 600_000

    @override_settings(PASSWORD_HASHERS=HASHERS)
    def test_a_new_hash_is_created_at_600_000_iterations(self):
        encoded = make_password("correct-horse-1")

        assert encoded.split("$")[1] == "600000"
        assert check_password("correct-horse-1", encoded)

    @override_settings(PASSWORD_HASHERS=HASHERS)
    def test_an_existing_1_000_000_iteration_hash_still_verifies(self):
        # Same algorithm as stock PBKDF2PasswordHasher (just a lower
        # iterations default), so a hash made before this change — or by
        # Django's own default hasher — must still check out correctly.
        from django.contrib.auth.hashers import PBKDF2PasswordHasher

        old_encoded = PBKDF2PasswordHasher().encode("correct-horse-1", "salt1234")

        assert check_password("correct-horse-1", old_encoded)
