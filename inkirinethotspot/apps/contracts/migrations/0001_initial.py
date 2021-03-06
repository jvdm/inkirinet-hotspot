# Generated by Django 3.1.6 on 2021-02-05 19:21

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Contract',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(blank=True, max_length=254, unique=True, verbose_name='email address')),
                ('first_name', models.CharField(max_length=150, verbose_name='first name')),
                ('last_name', models.CharField(max_length=150, verbose_name='last name')),
                ('is_active', models.BooleanField(default=True, help_text='Inactive contracts have all their devices disabled.', verbose_name='is active')),
                ('plan_type', models.CharField(choices=[('2MB', '2Mbps por dispositivo (ik$100)'), ('4MB', '4Mbps por dispositivo (ik$120)'), ('10MB', '10Mbps por dispositivo (ik$150)'), ('50MB', 'Mais velocidade (ik$150 + ik$10 por cada 1Mbps)')], default='2MB', help_text='The internet plan for this contract.', max_length=128, verbose_name='Internet Plan')),
                ('max_devices', models.PositiveIntegerField(default=2, help_text='The maximum number of devices allowed in this contract.', verbose_name='Maximum devices.')),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='Date and time when contract was created.', verbose_name='Created At')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='Last date and time when contract was updated.', verbose_name='Updated At')),
                ('user', models.ForeignKey(help_text='User this Contract belongs to.', on_delete=django.db.models.deletion.CASCADE, related_name='contracts', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Device',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('mac_address', models.CharField(max_length=17, null=True, unique=True)),
                ('description', models.CharField(help_text='A short device description.', max_length=150, verbose_name='description')),
                ('has_lease', models.BooleanField(default=False, help_text='Does this device have a static DHCP lease at Mikrotik?', verbose_name='has static lease')),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='Date and time when contract was created.', verbose_name='created At')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='Last date and time when contract was updated.', verbose_name='updated At')),
                ('contract', models.ForeignKey(help_text='Contract this device belongs to.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='devices', to='contracts.contract')),
            ],
        ),
    ]
