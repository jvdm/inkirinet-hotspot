import logging

from django.contrib.auth import views as auth_views
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import UserPassesTestMixin
from django.urls import reverse
from django.views.generic import FormView

from .forms import ContractLoginForm
from .forms import DevicesFormset


logger = logging.getLogger(__name__)


class OneToOneContractRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):

    def test_func(self):
        if self.request.user.contracts.exists():
            # Assume user and contract are 1:1.
            self.request.contract = self.request.user.contracts.first()
        else:
            self.request.contract = None
        return bool(self.request.contract)


class HomeView(OneToOneContractRequiredMixin, FormView):

    logger = logger.getChild('HomeView')

    template_name = 'contracts/home.html'

    form_class = DevicesFormset

    def get_success_url(self):
        return reverse('contracts:home')

    def get_request_ip(self):
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[-1].strip()
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.request.method in ('GET',):
            kwargs.update({
                'queryset': self.request.contract.devices.all()
            })
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(contract=self.request.contract)
        # Rename default form context attribute (would be nicer if FormMixin had
        # a hook for this).
        context['devices_formset'] = context.pop('form')
        return context

    def form_valid(self, devices_formset):
        contract = self.request.contract
        self.logger.info('Processing form: contract=%s', contract)
        devices_formset.save(commit=False)
        # To not allow new devices being added from the POST data, we process
        # the list manually.
        for device, _ in devices_formset.changed_objects:
            self.logger.info('To clean and save: contract=%s device=%s',
                             contract, device)
            device.save()
            self.logger.info('Saved: contract=%s device=%s',
                             contract, device)
        for device in devices_formset.deleted_objects:
            self.logger.info('To delete: contract=%s device=%s',
                             contract, device)
            device.delete()
            self.logger.info('Deleted: contract=%s device=%s',
                             contract, device)
        self.logger.info('Done.')
        return super().form_valid(devices_formset)


class LoginView(auth_views.LoginView):

    authentication_form = ContractLoginForm
    template_name = 'contracts/login.html'
