import binascii
import contextlib
import hashlib
import logging
import select
import socket
import ssl
import sys


logger = logging.getLogger(__name__)


class Mikrotik:
    """A wrapper around Mikrotik's API offering operations pertaining Inkirinet."""

    RATE_LIMIT = {
        '50MB': '100M/60M 100M/70M 100M/65M 90/90 8 100M/60M',
        '10MB': '100M/20M 100M/20M 100M/15M 90/90 8 100M/15M',
        '4MB': '100M/8M 100M/12M 100M/10M 90/90 8 100M/5M',
        '2MB': '100M/5M 100M/6M 100M/5M 90/90 8 100M/3M',
    }

    LEASE_COMMENT_SUFFIX = '@inkirinet'

    def __init__(self, api):
        self.api = api
        self.leases = {}

    def query_leases(self):
        """Query mikrotik's for all DHCP leases and return.

        :return: A dictionary containing all leases, where the key is the lease
                 id and the value is a dictionary with the lease attributes.
        """
        leases = {}
        for code, attrs in self.api.talk(['/ip/dhcp-server/lease/print']):
            if code == '!done':
                break
            if attrs['.id'] in leases:
                raise Exception(f"found two leases with the same id: "
                                f"one={attrs} two={leases[attrs['.id']]}")
            leases[attrs['.id']] = attrs
        return leases

    def poll_leases(self):
        """Query Mikrotik's DHCP leases and update the internal leases table.

        :return: A tuple with two lists with lease ids: The first one for
                 leases that were added since last poll and the second one
                 for leaseas that were removed since last poll.
        """
        leases = self.query_leases()
        new_keys = leases.keys() - self.leases.keys()
        deleted_keys = self.leases.keys() - leases.keys()
        self.leases = leases
        return new_keys, deleted_keys

    def create_static_lease(self, address_pool, email, device, rate):
        """Create a static lease in the address pool specified and rate."""
        lease = {
            'address': address_pool,
            'mac-address': device.upper(),
            'rate-limit': self.RATE_LIMIT[rate],
            'comment': f'{rate} {email} {self.LEASE_COMMENT_SUFFIX}'
        }
        static_lease = self.get_static_lease_by_mac_address(
            lease['address'],
            lease['mac-address'],
            ('.id', 'rate-limit', 'comment'))
        if static_lease:
            logger.info('static lease already created: %s', static_lease)
            if static_lease['comment'].strip().endswith(self.LEASE_COMMENT_SUFFIX):
                for reply, attrs in self.api.talk(
                        ['/ip/dhcp-server/lease/set',
                         f"=.id={static_lease['.id']}",
                         f"=address={lease['address']}",
                         f"=mac-address={lease['mac-address']}",
                         f"=rate-limit={lease['rate-limit']}",
                         f"=comment={lease['comment']}"]):
                    if reply == '!done':
                        break
                    else:
                        raise Exception(f"Failed to set lease: lease='{lease}': {reply} {attrs}")
        else:
            logger.info('creating static lease')
            for reply, attrs in self.api.talk(
                    ['/ip/dhcp-server/lease/add',
                     f"=address={lease['address']}",
                     f"=mac-address={lease['mac-address']}",
                     f"=rate-limit={lease['rate-limit']}",
                     f"=comment={lease['comment']}"]):
                if reply == '!done':
                    break
                else:
                    raise Exception(f"Failed to add lease: lease='{lease}': {reply} {attrs}")

        # Remove all the dynamic leases.

        for lease in self.list_dynamic_leases_by_mac_address(lease['mac-address']):
            self.remove_lease(lease)

    def remove_static_lease(self, address_pool, mac_address):
        static_lease = self.get_static_lease_by_mac_address(
            address_pool,
            mac_address.upper(),
            ('.id', 'rate-limit', 'comment'))
        if static_lease:
            self.remove_lease(static_lease)

    def remove_lease(self, lease):
        for reply, attrs in self.api.talk(['/ip/dhcp-server/lease/remove',
                                           f"=.id={lease['.id']}"]):
            if reply == '!done':
                return
            elif reply == '!trap' and 'no such item (4)' in attrs['message']:
                return
            else:
                raise Exception(f"Failed to remove lease: "
                                f"lease='{lease}' reply={reply} attrs={attrs}")

    def list_dynamic_leases_by_mac_address(self, mac_address, keys=None):
        if keys is None:
            keys = ['.id']
        ret = []
        for lease in self.leases.values():
            if (lease['dynamic'] == 'true'
                    and lease.get('mac-address', '').upper() == mac_address.upper()):
                ret.append({k: lease[k] for k in keys})
        return ret

    def get_static_lease_by_mac_address(self, address_pool, mac_address, keys=None):
        if keys is None:
            keys = ['.id']
        ret = []
        for lease in self.leases.values():
            if (lease['address'] == address_pool
                    and lease['dynamic'] == 'false'
                    and lease['mac-address'].upper() == mac_address.upper()):
                ret.append({k: lease[k] for k in keys})
        return ret[0] if ret else None

    def get_mac_address_by_dynamic_ip(self, ip_address):
        """Find the dynamic lease that has :param:`ip_address` as the active address."""
        for code, attrs in self.api.talk(['/ip/dhcp-server/lease/print',
                                          '?=status=bound',
                                          '?=dynamic=true',
                                          f'?=active-address={ip_address}',
                                          '=.proplist=mac-address']):
            if code == '!re':
                return attrs['mac-address']
            if code == '!done':
                break
            raise Exception(f'call to api failed: {code} {attrs}')
        return None


class ApiRos:
    """Routeros API."""

    def __init__(self, sk):
        self.sk = sk
        self.currenttag = 0
        self._read_buffer = b''

    def login(self, username, pwd):
        for repl, attrs in self.talk(["/login", "=name=" + username,
                                      "=password=" + pwd]):
            if repl == '!trap':
                return False
            elif '=ret' in attrs.keys():
                # for repl, attrs in self.talk(["/login"]):
                chal = binascii.unhexlify((attrs['=ret']).encode(sys.stdout.encoding))
                md = hashlib.md5()
                md.update(b'\x00')
                md.update(pwd.encode(sys.stdout.encoding))
                md.update(chal)
                for repl2, attrs2 in self.talk(["/login", "=name=" + username,
                                                "=response=00" + binascii.hexlify(
                                                    md.digest()).decode(sys.stdout.encoding)]):
                    if repl2 == '!trap':
                        return False
        return True

    def talk(self, words):
        if self.writeSentence(words) == 0: return
        r = []
        while 1:
            i = self.readSentence()
            if len(i) == 0:
                continue
            reply = i[0]
            attrs = {}
            for w in i[1:]:
                j = w.find('=', 1)
                if (j == -1):
                    attrs[w] = ''
                else:
                    attrs[w[:j].strip('=')] = w[j + 1:]
            r.append((reply, attrs))
            if reply == '!done':
                break
        return r

    def writeSentence(self, words):
        ret = 0
        for w in words:
            self.writeWord(w)
            ret += 1
        self.writeWord('')
        return ret

    def readSentence(self):
        r = []
        while 1:
            w = self.readWord()
            if w == '': return r
            r.append(w)

    def writeWord(self, w):
        logger.debug(("<<< " + w))
        self.writeLen(len(w))
        self.writeStr(w)

    def readWord(self):
        ret = self.readStr(self.readLen())
        logger.debug((">>> " + ret))
        return ret

    def writeLen(self, l):
        if l < 0x80:
            self.writeByte((l).to_bytes(1, sys.byteorder))
        elif l < 0x4000:
            l |= 0x8000
            tmp = (l >> 8) & 0xFF
            self.writeByte(((l >> 8) & 0xFF).to_bytes(1, sys.byteorder))
            self.writeByte((l & 0xFF).to_bytes(1, sys.byteorder))
        elif l < 0x200000:
            l |= 0xC00000
            self.writeByte(((l >> 16) & 0xFF).to_bytes(1, sys.byteorder))
            self.writeByte(((l >> 8) & 0xFF).to_bytes(1, sys.byteorder))
            self.writeByte((l & 0xFF).to_bytes(1, sys.byteorder))
        elif l < 0x10000000:
            l |= 0xE0000000
            self.writeByte(((l >> 24) & 0xFF).to_bytes(1, sys.byteorder))
            self.writeByte(((l >> 16) & 0xFF).to_bytes(1, sys.byteorder))
            self.writeByte(((l >> 8) & 0xFF).to_bytes(1, sys.byteorder))
            self.writeByte((l & 0xFF).to_bytes(1, sys.byteorder))
        else:
            self.writeByte((0xF0).to_bytes(1, sys.byteorder))
            self.writeByte(((l >> 24) & 0xFF).to_bytes(1, sys.byteorder))
            self.writeByte(((l >> 16) & 0xFF).to_bytes(1, sys.byteorder))
            self.writeByte(((l >> 8) & 0xFF).to_bytes(1, sys.byteorder))
            self.writeByte((l & 0xFF).to_bytes(1, sys.byteorder))

    def readLen(self):
        c = ord(self.readStr(1))
        # print (">rl> %i" % c)
        if (c & 0x80) == 0x00:
            pass
        elif (c & 0xC0) == 0x80:
            c &= ~0xC0
            c <<= 8
            c += ord(self.readStr(1))
        elif (c & 0xE0) == 0xC0:
            c &= ~0xE0
            c <<= 8
            c += ord(self.readStr(1))
            c <<= 8
            c += ord(self.readStr(1))
        elif (c & 0xF0) == 0xE0:
            c &= ~0xF0
            c <<= 8
            c += ord(self.readStr(1))
            c <<= 8
            c += ord(self.readStr(1))
            c <<= 8
            c += ord(self.readStr(1))
        elif (c & 0xF8) == 0xF0:
            c = ord(self.readStr(1))
            c <<= 8
            c += ord(self.readStr(1))
            c <<= 8
            c += ord(self.readStr(1))
            c <<= 8
            c += ord(self.readStr(1))
        return c

    def writeStr(self, str):
        n = 0
        while n < len(str):
            r = self.sk.send(bytes(str[n:], 'UTF-8'))
            if r == 0: raise RuntimeError("connection closed by remote end")
            n += r

    def writeByte(self, str):
        n = 0
        while n < len(str):
            r = self.sk.send(str[n:])
            if r == 0: raise RuntimeError("connection closed by remote end")
            n += r

    def readStr(self, length):
        while len(self._read_buffer) < length:
            s = self.sk.recv(4096)
            if s == b'': raise RuntimeError("connection closed by remote end")
            self._read_buffer += s
        s = self._read_buffer[:length]
        self._read_buffer = self._read_buffer[length:]
        return s.decode(sys.stdout.encoding, "replace")


def open_socket(dst, port, *, secure=False):
    skt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if secure:
        s = ssl.wrap_socket(skt, ssl_version=ssl.PROTOCOL_TLSv1_2,
                            ciphers="ADH-AES128-SHA256")  # ADH-AES128-SHA256
    else:
        s = skt
    s.connect((dst, port))
    return s


@contextlib.contextmanager
def connect(host, port, username, password, *, disable_ssl=False):
    secure = not disable_ssl
    sock = open_socket(host, port, secure=secure)
    api = ApiRos(sock)
    try:
        if not api.login(username, password):
            raise Exception(f"Connected to RouterOS API (Mikrotik), but "
                            "authentication failed: username='{username}' "
                            "password='{len(password) * '*'}'.")
        yield Mikrotik(api)
    finally:
        sock.close()


def parse_args():
    import argparse

    parser = argparse.ArgumentParser(
        'mikrotik',
        description="Mikrotik command line.")

    parser.add_argument(
        'host',
        help="The Mikrotik's RouterOS API host to connect.")
    parser.add_argument(
        '--disable-ssl',
        help=("Disable TLS/SSL connection, send all data through an "
              "unencrypted socket (Warning: This is unsafe, login "
              "credentials and all data will visible throught the "
              "network."),
        action='store_true')
    parser.add_argument(
        'port',
        help=("The Mikrotik's RouterOS API port to connect (default: 8729 or "
              "8728 if `--disable-ssl')."),
        nargs='?',
        default=None)

    args = parser.parse_args()

    if args.port is None:
        args.port = 8728 if args.disable_ssl else 8729

    return args


def main(args):
    s = open_socket(args.host, args.port, secure=not args.disable_ssl)
    apiros = ApiRos(s)
    if not apiros.login("api", "api"):
        return

    inputsentence = []
    while True:
        r = select.select([s, sys.stdin], [], [], None)
        if s in r[0]:
            print(apiros.readSentence())
        if sys.stdin in r[0]:
            # If empty line, send sentence and start with new otherwise
            # append to input sentence.
            line = sys.stdin.readline().strip()
            if line == '':
                apiros.writeSentence(inputsentence)
                inputsentence = []
            else:
                inputsentence.append(line)


if __name__ == '__main__':
    main(parse_args())
