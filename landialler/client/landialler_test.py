# $Id$


import os
import socket
import unittest
import xmlrpclib

import landialler
import mock


class ObservableTest(unittest.TestCase):

    def test_add(self):
        """Check we can add an observer"""
        observable = landialler.Observable()
        observer = mock.Mock()
        observable.add_observer(observer)
        observable.notify_observers()
        self.assertEqual(len(observer.getNamedCalls('update')), 1)

    def test_remove(self):
        """Check we can remove an existing observer"""
        observable = landialler.Observable()
        observer = mock.Mock()
        observable.add_observer(observer)
        observable.remove_observer(observer)
        observable.notify_observers()
        self.assertEqual(len(observer.getNamedCalls('update')), 0)


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

    def test_connect(self):
        """Check remote calls to connect() method"""
        server = mock.Mock()
        modem = landialler.RemoteModem(server)
        modem.connect()
        self.assertEqual(server.getNamedCalls('connect')[0].getParam(0),
                         modem.client_id)
        
    def test_disconnect(self):
        """Check remote calls to disconnect() method"""
        server = mock.Mock()
        modem = landialler.RemoteModem(server)
        modem.disconnect()
        call = server.getNamedCalls('disconnect')[0] 
        self.assertEqual(call.getParam(0), modem.client_id)
        # TODO: fix disconnect method to include all parameter
#         self.assertEqual(call.getParam('all'), False)

    def test_hang_up(self):
        """Check remote modem can hang up the modem"""
        server = mock.Mock({'disconnect': True})
        modem = landialler.RemoteModem(server)
        modem.disconnect_all()
        call = server.getNamedCalls('disconnect')[0] 
        self.assertEqual(call.getParam(0), modem.client_id)
        self.assertEqual(call.getParam('all'), True)

    def test_get_status(self):
        """Check remote calls to get_status() method are observable"""
        server = mock.Mock({'get_status': (2, True, 23)})
        modem = landialler.RemoteModem(server)
        observer = mock.Mock()
        modem.add_observer(observer)
        modem.connect()
        modem.get_status()
        self.assertEqual(len(observer.getNamedCalls('update')), 1)

    def test_read_status_from_modem(self):
        """Check modem status accessible to observers"""
        server = mock.Mock({'get_status': (2, True, 23)})
        modem = landialler.RemoteModem(server)
        modem.connect()
        modem.get_status()
        self.assertEqual(modem.num_users, 2)
        self.assertEqual(modem.is_connected, True)
        self.assertEqual(modem.seconds_online, 23)

    def test_read_status_when_interested(self):
        """Check get_status() only called when client is interested"""
        server = mock.Mock({'get_status': (1, True, 23)})
        modem = landialler.RemoteModem(server)
        self.assertEqual(len(server.getNamedCalls('get_status')), 0)
        modem.get_status()
        self.assertEqual(len(server.getNamedCalls('get_status')), 0)
        modem.connect()
        modem.get_status()
        self.assertEqual(len(server.getNamedCalls('get_status')), 1)
        modem.disconnect()
        modem.get_status()
        self.assertEqual(len(server.getNamedCalls('get_status')), 1)
        modem.disconnect_all()
        modem.get_status()
        self.assertEqual(len(server.getNamedCalls('get_status')), 1)

    def test_hang_up_sets_disconnected(self):
        """Check that modem doesn't appear to be connected after hang up"""
        server = mock.Mock({'get_status': (1, True, 23)})
        modem = landialler.RemoteModem(server)
        modem.connect()
        modem.get_status()
        self.assertEqual(modem.is_connected, True)
        modem.disconnect()
        self.assertEqual(modem.is_connected, False)
        

if __name__ == '__main__':
    unittest.main()
