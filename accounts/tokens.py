from django.contrib.auth.tokens import PasswordResetTokenGenerator


class EmailVerificationTokenGenerator(PasswordResetTokenGenerator):
    """
    Same mechanism as Django's password-reset token, but the hash also
    depends on `is_active`. That means once a token is used and the
    account is activated, that same token stops validating — no extra
    database model needed to track "used" tokens.
    """

    def _make_hash_value(self, user, timestamp):
        return f"{user.pk}{user.is_active}{timestamp}{user.email}"


account_activation_token = EmailVerificationTokenGenerator()
