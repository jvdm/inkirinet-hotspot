from django.test import TestCase

from .. import models


class TestContract(TestCase):

    def test_get_from_email_when_empty(self):
        email = 'foobar@example.com'
        with self.assertRaises(models.Contract.DoesNotExist):
            models.Contract.objects.get_from_email(email)

    def test_create_contract(self):
        email = 'foobar@example.com'
        contract = models.Contract.objects.create_contract(email)
        self.assertIsNotNone(contract)
        self.assertEquals(email, contract.email)

    def test_create_contract_and_get_from_email(self):
        email = 'foobar@example.com'
        contract = models.Contract.objects.create_contract(email)
        self.assertEquals(email, contract.user.username)
        db_contract = models.Contract.objects.get_from_email(contract.email)
        self.assertEquals(db_contract, contract)
