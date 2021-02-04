from django.contrib.auth import views as auth_views
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import UserPassesTestMixin
from django.views.generic.detail import DetailView

from .forms import ContractLoginForm


class ContractLoginRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):

    def test_func(self):
        return self.request.user.contracts.exists()


class HomeView(ContractLoginRequiredMixin, DetailView):

    template_name = 'contracts/home.html'

    def get_object(self, queryset=None):
        return self.request.user.contracts.first()


class LoginView(auth_views.LoginView):

    authentication_form = ContractLoginForm
    template_name = 'contracts/login.html'
