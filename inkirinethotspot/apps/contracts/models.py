import django.contrib.auth
from django.db import models
from django.db import transaction
from django.utils.translation import gettext_lazy as __


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

    def save(self, **kwds):
        with transaction.atomic():
            self.user, _ = User.objects.get_or_create(
                email=self.email,
                defaults={'username': self.email,
                          'first_name': self.first_name,
                          'last_name': self.last_name})
            super().save(**kwds)
