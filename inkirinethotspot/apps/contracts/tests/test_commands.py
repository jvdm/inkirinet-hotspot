from io import StringIO
from unittest import mock

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from inkirinet.sheets import Contract
from inkirinethotspot.apps.contracts import models


class LeaseSyncTest(TestCase):

    out = StringIO()

    def call_command(self):
        return call_command('inkirinetleasesync', stdout=self.out)

    @mock.patch('inkirinet.routeros.connect')
    def test_can_call(self, connect_mock):
        mikrotik = mock.MagicMock()
        connect_mock.return_value.__enter__.return_value = mikrotik
        self.call_command()
        mikrotik.poll_leases.assert_called_once()


class SheetsPollTest(TestCase):

    out = StringIO()

    def call_command(self):
        return call_command('inkirinetsheetspoll', stdout=self.out)

    @mock.patch('inkirinet.sheets.Spreadsheet')
    def test_can_call(self, SpreadsheetMock):
        contract = Contract('foo@bar', 'foo', '10MB', True, timezone.now(), 2, [])
        SpreadsheetMock.return_value \
            .read_all.return_value \
            .values.return_value = [contract]
        self.call_command()
        self.assertEquals(1, models.Contract.objects.count())
        self.assertEqual(contract.email, models.Contract.objects.first().email)
