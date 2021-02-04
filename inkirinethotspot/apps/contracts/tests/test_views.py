from django.contrib import auth
from django.test import TestCase
from django.urls import reverse

from .. import models


class TestPublicHome(TestCase):

    def test_when_get_then_redirect_to_login(self):
        url = reverse('contracts:home')
        response = self.client.get(url)
        self.assertRedirects(response,
                             reverse('contracts:login') + f'?next={url}')


class TestAuthenticatedHome(TestCase):
    url = reverse('contracts:home')

    def setUp(self):
        self.contract = (models.Contract
                         .objects.create_contract('foobar@example.com'))
        self.assertTrue(self.client.login(contract_email='foobar@example.com'))

    def test_when_get_then_template(self):
        response = self.get()
        self.assertIn('contracts/home.html',
                      [t.name for t in response.templates])

    def test_when_get_then_contract_in_context(self):
        response = self.get()
        contract = response.context.get('contract')
        self.assertIsNotNone(contract)
        self.assertEquals(self.contract, contract)
        self.assertContains(response, contract.full_name)

    def test_when_contract_inactive_and_no_devices_and_not_allowed(self):

        self.contract.is_active = False
        self.contract.max_devices = 0
        self.contract.save()

        response = self.get()

        self.assertContains(response, 'Inactive contracts have all their devices disabled')

        self.assertNotContains(response, 'Your contract allows')
        self.assertNotContains(response, 'Unfortunately, you cannot register new devices')
        self.assertNotContains(response, 'You can register')

        self.assertNotContains(response, "You haven't registered any devices yet")

    def test_when_contract_inactive_and_no_devices_and_allowed(self):

        self.contract.is_active = False
        self.contract.max_devices = 3
        self.contract.save()

        response = self.get()

        self.assertContains(response, 'Inactive contracts have all their devices disabled')

        self.assertNotContains(response, 'Your contract allows')
        self.assertNotContains(response, 'Unfortunately, you cannot register new devices')
        self.assertNotContains(response, 'You can register')

        self.assertNotContains(response, "You haven't registered any devices yet")

    def test_when_contract_inactive_and_devices_and_not_allowed(self):

        self.contract.is_active = False
        self.contract.max_devices = 0
        self.contract.save()

        self.contract.devices.create(mac_address='mac-address-foo')
        self.contract.devices.create(mac_address='max-address-bar')

        response = self.get()

        self.assertContains(response, 'Inactive contracts have all their devices disabled')

        self.assertNotContains(response, 'Your contract allows')
        self.assertNotContains(response, 'Unfortunately, you cannot register new devices')
        self.assertNotContains(response, 'You can register')

        self.assertNotContains(response, 'mac-address-foo')
        self.assertNotContains(response, 'mac-address-bar')

    def test_when_contract_inactive_and_devices_and_allowed(self):

        self.contract.is_active = False
        self.contract.max_devices = 3
        self.contract.save()

        self.contract.devices.create(mac_address='mac-address-foo')
        self.contract.devices.create(mac_address='max-address-bar')

        response = self.get()

        self.assertContains(response, 'Inactive contracts have all their devices disabled')

        self.assertNotContains(response, 'Your contract allows')
        self.assertNotContains(response, 'Unfortunately, you cannot register new devices')
        self.assertNotContains(response, 'You can register')

        self.assertNotContains(response, 'mac-address-foo')
        self.assertNotContains(response, 'mac-address-bar')

    def test_when_contract_active_and_no_devices_and_not_allowed(self):

        self.contract.is_active = True
        self.contract.max_devices = 0
        self.contract.save()

        response = self.get()

        self.assertNotContains(response, 'Inactive contracts have all their devices disabled')
        
        self.assertContains(response, 'Your contract allows <strong>0</strong> devices.')
        
        self.assertNotContains(response, 'You have <strong>0</strong> device registered')
        self.assertContains(response, "You haven't registered any devices yet")

        self.assertContains(response, 'Unfortunately, you cannot register new devices')
        self.assertNotContains(response, 'You can register <strong>2</strong> additional device')

    def test_when_contract_active_and_no_devices_and_allowed(self):

        self.contract.is_active = True
        self.contract.max_devices = 3
        self.contract.save()

        response = self.get()

        self.assertNotContains(response, 'Inactive contracts have all their devices disabled')

        self.assertContains(response, 'Your contract allows <strong>3</strong> devices.')

        self.assertNotContains(response, 'You have <strong>0</strong> device registered')
        self.assertContains(response, "You haven't registered any devices yet")

        self.assertNotContains(response, 'Unfortunately, you cannot register new devices')
        self.assertContains(response, 'You can register <strong>3</strong> additional device')

    def test_when_contract_active_and_devices_and_not_allowed(self):

        self.contract.is_active = True
        self.contract.max_devices = 0
        self.contract.save()

        self.contract.devices.create(mac_address='mac-address-foo')
        self.contract.devices.create(mac_address='max-address-bar')

        response = self.get()

        self.assertNotContains(response, 'Inactive contracts have all their devices disabled')

        self.assertContains(response, 'Your contract allows <strong>0</strong> devices.')

        self.assertContains(response, 'You have <strong>2</strong> devices registered')
        self.assertNotContains(response, "You haven't registered any devices yet")

        self.assertContains(response, 'Unfortunately, you cannot register new devices')
        self.assertNotContains(response, 'You can register <strong>3</strong> additional device')

        self.assertContains(response, '<td>mac-address-foo</td>', html=True)
        self.assertContains(response, '<td>max-address-bar</td>', html=True)

    def test_when_contract_active_and_devices_and_allowed(self):

        self.contract.is_active = True
        self.contract.max_devices = 3
        self.contract.save()

        self.contract.devices.create(mac_address='mac-address-foo')
        self.contract.devices.create(mac_address='max-address-bar')

        response = self.get()

        self.assertNotContains(response, 'Inactive contracts have all their devices disabled')

        self.assertContains(response, 'Your contract allows <strong>3</strong> devices.')

        self.assertContains(response, 'You have <strong>2</strong> devices registered')
        self.assertNotContains(response, "You haven't registered any devices yet")

        self.assertNotContains(response, 'Unfortunately, you cannot register new devices')
        self.assertContains(response, 'You can register <strong>1</strong> additional device')

        self.assertContains(response, '<td>mac-address-foo</td>', html=True)
        self.assertContains(response, '<td>max-address-bar</td>', html=True)

    def get(self):
        response = self.client.get(self.url)
        self.assertEquals(200, response.status_code)
        return response


class TestLoginView(TestCase):

    url = reverse('contracts:login')

    def test_when_get_then_template(self):
        response = self.client.get(self.url)
        self.assertEquals(200, response.status_code)
        self.assertIn('contracts/login.html',
                      [t.name for t in response.templates])

    def test_when_get_then_form(self):
        response = self.client.get(self.url)
        self.assertIsNotNone(response.context.get('form'))

    def test_when_post_empty_then_form_error(self):
        response = self.client.post(self.url)
        self.assertFormError(response, 'form', 'email',
                             'This field is required.')

    def test_when_post_without_contract_then_form_error(self):
        email = 'foobar@example.com'
        response = self.client.post(self.url, data={'email': email})
        self.assertFormError(response, 'form', '__all__',
                             'Sorry, this contract was not found.')

    def test_when_post_existing_contract_email_then_login(self):
        email = 'foobar@example.com'
        models.Contract.objects.create_contract(email)
        response = self.client.post(self.url, {'email': email})
        self.assertRedirects(response, reverse('contracts:home'))
        self.assertTrue(auth.get_user(self.client).is_authenticated)
