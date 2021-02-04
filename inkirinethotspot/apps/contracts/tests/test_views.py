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

    def test_when_get_without_devices_then_empty_table(self):
        response = self.get()
        self.assertContains(
            response,
            "You haven't registered any devices yet.")

    def test_when_get_with_devices_then_show_table(self):
        self.contract.devices.create(mac_address='weird-mac-address')
        response = self.get()
        self.assertContains(
            response,
            "weird-mac-address")
        self.assertNotContains(
            response,
            "You haven't registered any devices yet.")

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
