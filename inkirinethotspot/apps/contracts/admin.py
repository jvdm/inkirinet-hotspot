from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as __

from .models import Contract
from .models import Device


class ContractsAdminSite(admin.AdminSite):

    site_title = __('Inkirinet Administration')

    site_header = __('Inkirinet Administration')

    index_title = None


site = ContractsAdminSite()


class DevicesInline(admin.TabularInline):

    model = Device

    fields = ('description', 'mac_address', 'has_lease')

    readonly_fields = ('has_lease',)

    extra = 1


@admin.register(Contract, site=site)
class ContractAdmin(admin.ModelAdmin):

    date_hierarchy = 'created_at'

    list_select_related = True

    list_display = ('full_name',
                    'email',
                    'plan_type',
                    'is_active',
                    'max_devices',
                    'devices_view',
                    'created_at',
                    'updated_at')

    exclude = ('user',)

    list_filter = ('is_active',)

    inlines = [DevicesInline]

    search_fields = ('email', 'first_name', 'last_name')

    def devices_view(self, obj):
        return format_html(
            '<br />'.join(f'{i + 1}. {d.mac_address}'
                          for i, d in enumerate(obj.devices.all())))

    devices_view.short_description = 'Devices'
