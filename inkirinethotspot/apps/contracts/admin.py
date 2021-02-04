from django.contrib import admin
from django.utils.translation import ugettext_lazy as __

from .models import Contract


class ContractsAdminSite(admin.AdminSite):

    site_title = __('Inkirinet Administration')

    site_header = __('Inkirinet Administration')

    index_title = None


site = ContractsAdminSite()


@admin.register(Contract, site=site)
class ContractAdmin(admin.ModelAdmin):

    list_display = ['full_name', 'email']

    search_fields = ['email', 'first_name', 'last_name']

    exclude = ['user']
