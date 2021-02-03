from django.contrib.auth.backends import ModelBackend

from ..contracts import models


class ContractsAuthenticationBackend(ModelBackend):
    """Auth user's based on contracts."""

    def authenticate(self, request, contract_email=None, **kwargs):
        """Auth if there is a contract with the specified e-mail."""
        try:
            contract = models.Contract.objects.get_from_email(contract_email)
        except models.Contract.DoesNotExist:
            return None
        user = contract.user
        if user and self.user_can_authenticate(user):
            return user
        return None
