from io import StringIO
from unittest import mock

from django.core.management import call_command
from django.test import TestCase


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
