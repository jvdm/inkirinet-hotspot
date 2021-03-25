import datetime
import logging

from google.oauth2 import service_account
from googleapiclient import discovery


logger = logging.getLogger(__name__)


class Spreadsheet:
    """A wrapper around Google Spreadsheet APIs."""

    logger = logger.getChild('Spreadsheet')

    def __init__(self, key_file, spreadsheet_id):
        credentials = service_account.Credentials.from_service_account_file(key_file)
        self.sheets = discovery.build('sheets',
                                      'v4',
                                      credentials=credentials,
                                      cache_discovery=False) \
                               .spreadsheets()
        self.spreadsheet_id = spreadsheet_id

    def read_all(self):
        result = self.sheets \
                     .values() \
                     .get(spreadsheetId=self.spreadsheet_id, range='A:R') \
                     .execute()
        contracts = []
        # Ignore first row: header.
        for row in result['values'][1:]:
            try:
                contract = self._create_contract_from_row(row)
            except ValueError:
                logging.error("Invalid contract row, ignoring: %s", row)
                continue
            contracts.append(contract)
        ret = {}
        for contract in sorted(contracts, key=lambda c: c.created_at):
            if contract.email in ret:
                logger.error("Duplicated e-mail found in the contract database, ignoring: "
                             "original=%s duplicate=%s",
                             repr(ret[contract.email]),
                             repr(contract))
                continue
            ret[contract.email] = contract
        return ret

    @staticmethod
    def _create_contract_from_row(row):
        if len(row) < 18:
            row.extend([''] * (18 - len(row)))

        plan_type = row[1].split(' ', 1)[0].upper().rstrip('PS')

        # The plan "Mais velocidade (ik$150 + ik$10 por cada 1Mbps)"
        # is converted to "MAI" then mapped into "50MB", all the other
        # plans start with the MB and are parsed accordingly.
        if plan_type == 'MAI':
            plan_type = '50MB'

        max_devices = int(row[2].strip().split(' ', 1)[0])

        name = row[4].strip().title()

        email = row[6].lower()

        # Plans are marked as "active" when being imported.
        active = True

        # Force UTC-3 given the database was created in Brazilian timezone.
        created_at = datetime.datetime.strptime(row[0] + ' -0300', '%d/%m/%Y %H:%M:%S %z')

        devices = { mac.strip().upper().split(' - ')[0]
                    for mac in row[8].split('\n')
                    if mac }

        return Contract(email,
                        name,
                        plan_type,
                        active,
                        created_at,
                        max_devices,
                        devices)


class Contract:
    """A model class representing a single plan contract for InkiriNet."""

    PLAN_TYPES = ('2MB', '4MB', '10MB', '10MB+')

    def __init__(self, email, name, plan_type, active, created_at, max_devices, devices):
        self.name = name
        if plan_type not in self.PLAN_TYPES:
            raise ValueError(f"Invalid internet plan: '{plan_type}'.")
        if type(active) is not bool:
            raise ValueError(f"Invalid `active` flag: '{active}'.")
        if email in (None, ''):
            raise ValueError(f"Invalid e-mail: '{email}'.")
        self.created_at = created_at
        self.email = email
        self.plan_type = plan_type
        self.active = active
        self.max_devices = max_devices
        self.devices = devices

    def __str__(self):
        return f"{self.email}: {self.devices}"

    def __repr__(self):
        params = ', '.join(repr(getattr(self, f))
                           for f in ('email',
                                     'plan_type',
                                     'active',
                                     'created_at',
                                     'devices'))
        return f"{self.__class__.__name__}({params})"
