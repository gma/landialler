# $Id$


import os
import socket
import unittest
import xmlrpclib

import landialler
import mock


class RemoteModemTest(unittest.TestCase):

    def test_client_id(self):
        """Check remote modem can use an IP address as a client ID"""
        modem = landialler.RemoteModem(mock.Mock())
        ip = socket.gethostbyname(socket.gethostname())
        if 'USER' in os.environ:
            try:
                user_var = os.environ['USER']
                del os.environ['USER']
                self.assertEqual(modem.client_id, ip)
            finally:
                os.environ['USER'] = user_var
        else:
            self.assertEqual(modem.client_id, ip)

    def test_client_id_with_user(self):
        """Check client ID incorporates user name (if available)"""
        if not 'USER' in os.environ:
            return
        server = mock.Mock()
        modem = landialler.RemoteModem(server)
        ip = socket.gethostbyname(socket.gethostname())
        user = os.environ['USER']
        self.assertEqual(modem.client_id, '%s@%s' % (user, ip))

    def test_dial(self):
        """Check remote calls to dial() method"""
        server = mock.Mock({'dial': True})
        modem = landialler.RemoteModem(server)
        self.assertEqual(modem.dial(), True)
        self.assertEqual(server.getNamedCalls('dial')[0].getParam(0),
                         modem.client_id)
        
    def test_hang_up(self):
        """Check remote calls to hang_up() method"""
        server = mock.Mock({'hang_up': True})
        modem = landialler.RemoteModem(server)
        self.assertEqual(modem.hang_up(), True)
        self.assertEqual(server.getNamedCalls('hang_up')[0].getParam(0),
                         modem.client_id)

    def test_get_status(self):
        """Check remote calls to get_status() method"""
        server = mock.Mock({'get_status': (2, True, 23)})
        modem = landialler.RemoteModem(server)
        self.assertEqual(modem.get_status(), (2, True, 23))
        self.assertEqual(server.getNamedCalls('get_status')[0].getParam(0),
                         modem.client_id)


if __name__ == '__main__':
    unittest.main()
