import unittest
from unittest import mock

from .sheets import Spreadsheet


class SpreadsheetTest(unittest.TestCase):

    sheets_mock = mock.MagicMock()
    discovery_mock = mock.MagicMock()
    discovery_mock.return_value.spreadsheets.return_value = sheets_mock

    @mock.patch('googleapiclient.discovery.build', discovery_mock)
    def test_read_all_if_(self):
        (self.sheets_mock
             .values.return_value
             .get.return_value
             .execute.return_value) = {'values': [
                 None,
                 ('01/01/2020 13:08:10',
                  '10Mbps por dispositivo (ik$150)',
                  '2 (Padrão, sem custo adicional)',
                  '',
                  'FOO BAR',
                  '',
                  'foo@bar.com',
                  'Estou de acordo',
                  '',
                  'TRUE',
                  'TRUE',
                  'TRUE',
                  'TRUE',
                  '01/01/2020',
                  '01/01/2020',
                  '0',
                  '0',
                  '0')
             ]}
        with mock.patch('google.oauth2.service_account.Credentials.from_service_account_file'):
            spreadsheet = Spreadsheet('/dev/null', None)
        ret = spreadsheet.read_all()
        self.assertTrue(ret['foo@bar.com'].active)


if __name__ == '__main__':
    unittest.main()
