from django.test import TestCase

from .. import auth
from .. import models


class TestContractsAuthenticationBackend(TestCase):

    def test_authenticate_when_no_contract_then_fails(self):
        backend = auth.ContractsAuthenticationBackend()
        user = backend.authenticate(None, 'foobar@example.com')
        self.assertIsNone(user)

    def test_authenticate_when_contract_exists_then_success(self):
        email = 'foobar@example.com'
        models.Contract.objects.create_contract(email)
        backend = auth.ContractsAuthenticationBackend()
        user = backend.authenticate(None, 'foobar@example.com')
        self.assertIsNotNone(user)

    def test_authenticate_when_contract_exists_but_bad_credential_then_fail(self):
        email = 'foobar@example.com'
        models.Contract.objects.create_contract(email)
        backend = auth.ContractsAuthenticationBackend()
        user = backend.authenticate(None, 'somethingelse')
        self.assertIsNone(user)

    def test_authenticate_when_contract_exists_but_user_is_inactive(self):
        email = 'foobar@example.com'
        contract = models.Contract.objects.create_contract(email)
        contract.user.is_active = False
        contract.user.save()
        backend = auth.ContractsAuthenticationBackend()
        user = backend.authenticate(None, email)
        self.assertIsNone(user)
