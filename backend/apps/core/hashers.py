from django.contrib.auth.hashers import PBKDF2PasswordHasher


class OwaspPBKDF2PasswordHasher(PBKDF2PasswordHasher):
    """Django 5.2's default (1,000,000 iterations) assumes real server CPU.
    On Render's free tier (shared/throttled vCPU), that alone made every
    login take 3-4.5s — confirmed by timing /api/auth/token/ against a
    nonexistent username, where Django deliberately runs the hasher anyway
    (a dummy check, so failed logins don't leak which usernames exist via
    timing). 600,000 iterations matches OWASP's current PBKDF2-SHA256
    minimum and Django's own 5.0 default — meaningfully faster without
    dropping below the recommended floor.

    Same `algorithm` as the stock hasher, so this doesn't orphan existing
    hashes: Django reads the iteration count back out of each stored hash
    string at verify time (not from this class), and transparently
    re-hashes at 600,000 on a user's next successful login.
    """

    iterations = 600_000
