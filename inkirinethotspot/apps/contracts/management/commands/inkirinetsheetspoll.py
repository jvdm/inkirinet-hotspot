from django.conf import settings
from django.core.management.base import BaseCommand
from inkirinethotspot.apps.contracts import models
from inkirinet.sheets import Spreadsheet


class Command(BaseCommand):

    help = "Poll contracts from the Google's Spreadsheet."

    def handle(self, *args, **options):
        sheet = Spreadsheet(**settings.GOOGLE_SHEETS)
        for sheet_contract in sheet.read_all().values():
            first_name = sheet_contract.name
            last_name = ''
            if ' ' in first_name:
                first_name, last_name = first_name.split(' ', 1)
            contract, created = models.Contract.objects.get_or_create(
                email=sheet_contract.email,
                defaults={
                    'first_name': first_name,
                    'last_name': last_name,
                    'plan_type': sheet_contract.plan_type,
                    'is_active': sheet_contract.active,
                    'max_devices': sheet_contract.max_devices,
                })
            if created:
                self.stdout.write(self.style.SUCCESS(f"New contract: {contract}."))
                for mac_address in sheet_contract.devices:
                    device, _ = models.Device.objects.get_or_create(
                        mac_address=mac_address,
                        defaults={'contract': contract})
