import logging

import django.contrib.auth
from django.conf import settings
from django.db import models
from django.db import transaction
from django.utils.translation import gettext_lazy as __

from inkirinet import routeros


logger = logging.getLogger(__name__)

User = django.contrib.auth.get_user_model()


class ContractManager(models.Manager):
    """Contract model's custom manager."""

    def get_from_email(self, email):
        """Get a Contract from its user's email address."""
        return self.get(user__username=email)

    def create_contract(self, email, **extra_attrs):
        """Create a new contract and its attached user."""
        contract = Contract(email=email, **extra_attrs)
        contract.save()
        return contract

    def create(self, **kwds):
        return self.create_contract(**kwds)


class Contract(models.Model):

    objects = ContractManager()

    email = models.EmailField(
        __('email address'),
        blank=True,
        unique=True)

    first_name = models.CharField(
        __('first name'),
        max_length=150)

    last_name = models.CharField(
        __('last name'),
        max_length=150)

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='contracts',
        help_text=__('User this Contract belongs to.'))

    is_active = models.BooleanField(
        default=True,
        verbose_name=__('is active'),
        help_text=__('Inactive contracts have all their devices disabled.'))

    PLAN_2MB = '2MB'
    PLAN_4MB = '4MB'
    PLAN_10MB = '10MB'
    PLAN_50MB = '50MB'

    PLAN_TYPES = [
        (PLAN_2MB, __('2Mbps por dispositivo (ik$100)')),
        (PLAN_4MB, __('4Mbps por dispositivo (ik$120)')),
        (PLAN_10MB, __('10Mbps por dispositivo (ik$150)')),
        (PLAN_50MB, __('Mais velocidade (ik$150 + ik$10 por cada 1Mbps)'))
    ]

    plan_type = models.CharField(
        max_length=128,
        choices=PLAN_TYPES,
        default=PLAN_2MB,
        verbose_name=__('Internet Plan'),
        help_text=__('The internet plan for this contract.'))

    max_devices = models.PositiveIntegerField(
        default=2,
        verbose_name=__('Maximum devices.'),
        help_text=__('The maximum number of devices allowed in this contract.'))

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=__('Created At'),
        help_text=__('Date and time when contract was created.'))

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=__('Updated At'),
        help_text=__('Last date and time when contract was updated.'))

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def has_devices(self):
        return self.devices.exists()

    @property
    def devices_count(self):
        return self.devices.count()

    @property
    def devices_allowed(self):
        allowed = self.max_devices - self.devices_count
        return allowed if allowed >= 0 else 0

    def save(self, **kwds):
        with transaction.atomic():
            self.user, _ = User.objects.get_or_create(
                username=self.email,
                defaults={'email': self.email,
                          'first_name': self.first_name,
                          'last_name': self.last_name})
            super().save(**kwds)

    def __str__(self):
        return f'{self.full_name} <{self.email}>'


class DeviceManager(models.Manager):

    logger = logger.getChild('DeviceManager')

    def get_or_create_from_ip(self, contract, ip_address):
        with routeros.connect(**settings.ROUTEROS_API) as api:
            mac_address = api.get_mac_address_by_dynamic_ip(ip_address)
        if mac_address is None:
            self.logger.error('add(): could not find the active address for '
                              'the ip provided, ignoring request: ip_address=%s',
                              ip_address)
            return
        logger.info('add(): found active mac address: ip=%s mac_address=%s',
                    ip_address, mac_address)
        device, created = self.get_or_create(
            mac_address=mac_address,
            defaults={'contract': contract,
                      'has_lease': False})
        if created:
            logger.info("add(): created a new device: device='%s' "
                        "contract='%s' has_lease=%s",
                        device, device.contract, device.has_lease)
        elif device.contract != contract:
            logger.error("add(): device belongs to a different contract, "
                         "ignoring: device='%s' contract='%s' has_lease=%s",
                         device, device.contract, device.has_lease)
        else:
            logger.error("add(): device already belong to this contract, "
                         "ignoring: device='%s' contract='%s' has_lease=%s",
                         device, device.contract, device.has_lease)


class Device(models.Model):

    objects = DeviceManager()

    contract = models.ForeignKey(
        Contract,
        related_name='devices',
        on_delete=models.SET_NULL,
        null=True,
        help_text=__('Contract this device belongs to.'))

    mac_address = models.CharField(
        max_length=17,
        unique=True,
        null=True)

    description = models.CharField(
        max_length=150,
        verbose_name=__('description'),
        help_text=__('A short device description.'))

    has_lease = models.BooleanField(
        default=False,
        verbose_name=__('has static lease'),
        help_text=__('Does this device have a static DHCP lease at Mikrotik?'))

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=__('created At'),
        help_text=__('Date and time when contract was created.'))

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=__('updated At'),
        help_text=__('Last date and time when contract was updated.'))

    def __str__(self):
        return f'{self.mac_address}'
