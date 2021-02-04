from django.test import TestCase

from .. import models


class TestContract(TestCase):

    email = 'foobar@example.com'
    
    def test_get_from_email_when_empty(self):
        with self.assertRaises(models.Contract.DoesNotExist):
            models.Contract.objects.get_from_email(self.email)

    def test_create_contract(self):
        contract = self.create_contract()
        self.assertIsNotNone(contract)
        self.assertEquals(self.email, contract.email)

    def test_create_contract_and_get_from_email(self):
        contract = self.create_contract()
        self.assertEquals(self.email, contract.user.username)
        db_contract = models.Contract.objects.get_from_email(contract.email)
        self.assertEquals(db_contract, contract)

    def test_has_devices(self):
        contract = self.create_contract()
        self.assertFalse(contract.has_devices)
        contract.devices.create(mac_address='foobar')
        self.assertTrue(contract.has_devices)

    def test_devices_count(self):
        contract = self.create_contract()
        contract.devices.create(mac_address='foo')
        contract.devices.create(mac_address='bar')
        self.assertEquals(2, contract.devices_count)

    def test_devices_allowed(self):
        contract = self.create_contract()
        contract.max_devices = 2
        contract.save()
        contract.devices.create(mac_address='foo')
        contract.devices.create(mac_address='bar')
        self.assertEquals(0, contract.devices_allowed)

    def test_devices_allowed_with_extra_devices(self):
        contract = self.create_contract()
        contract.max_devices = 0
        contract.save()
        contract.devices.create(mac_address='foo')
        contract.devices.create(mac_address='bar')
        self.assertEquals(0, contract.devices_allowed)

    def create_contract(self):
        email = 'foobar@example.com'
        contract = models.Contract.objects.create_contract(email)
        return contract
