from django.conf import settings
from django.core.management.base import BaseCommand

from inkirinet import routeros
from inkirinethotspot.apps.contracts.models import Device


class Command(BaseCommand):

    help = "Sync all leases from the devices in the contracts."

    ADDRESS_POOL = 'pool-Manual'

    def handle(self, *args, **options):
        with routeros.connect(**settings.ROUTEROS_API) as api:
            api.poll_leases()
            for device in Device.objects.all():
                self.stdout.write(f"At {device} of {device.contract}\n")
                self.handle_device(api, device)

    def handle_device(self, api, device):

        # Each device has two boolean flags:
        #
        # 1. CONTRACT: True if it is associated with an active contract,
        #    otherwise False.
        #
        # 2. HAS LEASE: True if it has a static DHCP lease in the router,
        #    otherwise False.
        #
        # Thus:
        #
        # | CONTRACT | HAS LEASE | Actions                                  |
        # |----------+-----------+------------------------------------------|
        # | TRUE     | TRUE      | Mark device as active.                   |
        # | TRUE     | FALSE     | Add static lease, remove dynamic leases. |
        # | FALSE    | TRUE      | Remove static lease, mark as inactive.   |
        # | FALSE    | FALSE     | Delete device in the database[1].        |
        #
        # [1]: We don't delete if contract is marked as "inactive", we want to
        #      keep devices in the DB without leases if contract is
        #      re-activated.  Meaning we only delete devices that are
        #      "orphaned".

        has_lease = api.get_static_lease_by_mac_address(
                        self.ADDRESS_POOL,
                        device.mac_address) is not None

        is_contracted = device.contract is not None and device.contract.is_active

        if is_contracted:
            if has_lease:
                device.is_active = True
                device.save()
            else:
                api.create_static_lease(self.ADDRESS_POOL,
                                        device.contract.email,
                                        device.mac_address,
                                        device.contract.plan_type)
                self.stdout.write(
                    self.style.SUCCESS(
                        f'New static lease created: {device.contract} {device}'))
        else:
            if has_lease:
                api.remove_static_lease(self.ADDRESS_POOL, device.mac_address)
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Static lease removed: {device.contract} {device}'))
            # If device belongs to a contract, keep it so re-enabling contract
            # will bring up the devices automatically.
            if device.contract:
                device.is_active = False
                device.save()
            else:
                device.delete()
                self.stdout.write(
                    self.style.WARNING(
                        f'Deleted orphaned device: {device}'))
