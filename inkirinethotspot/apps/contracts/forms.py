from django import forms
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as __


class ContractLoginForm(forms.Form):
    """The home contract form used to login users."""

    email = forms.EmailField(label='')

    error_messages = {
        'failed': __('Sorry, this contract was not found.'),
    }

    def __init__(self, request=None, *args, **kwds):
        self.request = request
        self.contract = None
        super().__init__(*args, **kwds)

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        if email is not None:
            user = authenticate(self.request, contract_email=email)
            if user is None:
                raise ValidationError(self.error_messages['failed'])
            # TODO In a world where multiple contracts exists per user, this
            #      will need revisiting.
            self.contract = user.contracts.first()
        return cleaned_data

    def get_user(self):
        return self.contract.user
