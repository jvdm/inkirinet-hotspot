from django.test import TestCase

from .. import forms
from .. import models


class TestHomeForm(TestCase):

    def test_get_contract_from_email_when_doesnt_exist_then_not_valid(self):
        email = 'foobar@example.com'
        form = forms.ContractLoginForm(data={'email': email})
        self.assertFalse(
            form.is_valid(),
            'There is no contract in DB, form should not be valid.')
        self.assertIn('Sorry, this contract was not found.',
                      form.errors['__all__'])

    def test_get_contract_from_email_when_exist_then_valid(self):
        email = 'foobar@example.com'
        models.Contract.objects.create_contract(email)
        form = forms.ContractLoginForm(data={'email': email})
        self.assertTrue(form.is_valid())
        self.assertEquals(email, form.contract.email)
        self.assertTrue(form.contract.user.is_authenticated)
