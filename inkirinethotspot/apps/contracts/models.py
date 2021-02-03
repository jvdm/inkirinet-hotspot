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
        # Currently we enforce 1:1 relationship with Users.  Moving
        # away from this would mean using a "get or create" from users
        # or a different business logic to create users first then
        # contracts.
        user_fields = ('first_name', 'last_name')
        user_attrs = {
            f: extra_attrs[f]
                for f in user_fields
                if f in extra_attrs
        }
        with transaction.atomic():
            user = User.objects.create_user(
                       username=email,
                       email=email,
                       **user_attrs)
            contract = Contract.objects.create(user=user, **extra_attrs)
        return contract


class Contract(models.Model):

    objects = ContractManager()

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
    def email(self):
        return self.user.email
