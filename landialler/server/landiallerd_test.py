# $Id$


import time
import unittest
import xmlrpclib

import landiallerd


class MockConfigParser:

    value = 'value from config file'

    def read(self, files):
        print 'mock running'

    def get(self, section, option):
        return self.value
    

class MockModem(landiallerd.SharedModem):

    # TODO: Call base class' init method, remove our count_clients()?

    def __init__(self, is_connected=False, is_connecting=False,
                 connect_command=True):
        self.num_clients = 0
        self._is_connected = is_connected
        self.is_connecting = is_connecting
        self._command_rval = connect_command

    def is_connected(self):
        return self._is_connected

    def run_connect_command(self):
        return self._command_rval

    def count_client(self):
        return self.num_clients


class MockOsModule:

    rval = None

    def system(self, *args):
        return self.rval


class MockTime:

    def __init__(self, offset):
        self._offset = offset

    def time(self):
        return time.time() + self._offset


class SharedModemTest(unittest.TestCase):

    def test_remember_client(self):
        """Check we can remember a client"""
        modem = landiallerd.SharedModem(MockConfigParser())
        modem.remember_client('127.0.0.1')
        self.assertEqual(modem.count_clients(), 1)
        modem.remember_client('127.0.0.1')
        self.assertEqual(modem.count_clients(), 1)
        modem.remember_client('127.0.0.2')
        self.assertEqual(modem.count_clients(), 2)

    def test_forget_client(self):
        """Check we can forget clients"""
        modem = landiallerd.SharedModem(MockConfigParser())
        modem.remember_client('127.0.0.1')
        modem.remember_client('127.0.0.2')
        modem.remember_client('127.0.0.3')
        self.assertEqual(modem.count_clients(), 3)
        modem.forget_client('127.0.0.2')
        self.assertEqual(modem.count_clients(), 2)
        modem.forget_all_clients()
        self.assertEqual(modem.count_clients(), 0)

    def test_list_clients(self):
        """Check we can list all clients"""
        modem = landiallerd.SharedModem(MockConfigParser())
        ip1 = '127.0.0.1'
        ip2 = '127.0.0.2'
        modem.remember_client(ip1)
        modem.remember_client(ip2)
        clients = modem.list_clients()
        clients.sort()
        self.assertEqual(clients, [ip1, ip2])

    def test_forget_old_clients(self):
        """Check that old clients are forgotten about automatically"""
        modem = landiallerd.SharedModem(MockConfigParser())
        modem.remember_client('127.0.0.1')
        real_time, landiallerd.time = landiallerd.time, MockTime(3600)
        try:
            self.assertEqual(modem.count_clients(), 1)
            modem.forget_old_clients()
            self.assertEqual(modem.count_clients(), 0)
        finally:
            landiallerd.time = real_time        

    def test_connect_command(self):
        """Check that we test the return value of the connect command"""
        modem = landiallerd.SharedModem(MockConfigParser())
        mock_os = MockOsModule()
        real_os, landiallerd.os = landiallerd.os, mock_os
        try:
            mock_os.rval = 0
            rval = modem.run_connect_command()
            self.assertEqual(rval, True)

            mock_os.rval = 1
            rval = modem.run_connect_command()
            self.assertEqual(rval, False)
        finally:
            landiallerd.os = real_os


class APITest(unittest.TestCase):

    def test_connect_when_connected(self):
        """Check the API's connect procedure when connected"""
        modem = MockModem(is_connected=True)
        api = landiallerd.API(modem)
        self.assertEqual(api.connect('127.0.0.1'), xmlrpclib.True)

    def test_connect_when_connecting(self):
        """Check the API's connect procedure when connecting"""
        modem = MockModem(is_connecting=True)
        api = landiallerd.API(modem)
        self.assertEqual(api.connect('127.0.0.1'), xmlrpclib.False)
        
    def test_connect_when_disconnected(self):
        """Check the API's connect procedure when not connected"""
        modem = MockModem(connect_command=True)
        api = landiallerd.API(modem)
        self.assertEqual(api.connect('127.0.0.1'), xmlrpclib.True)

        modem = MockModem(connect_command=False)
        api = landiallerd.API(modem)
        self.assertEqual(api.connect('127.0.0.1'), xmlrpclib.False)

    def test_disconnect_not_connected(self):
        """Check the API's disconnect procedure when not connected"""
        modem = MockModem()
        modem.num_clients = 0
        raise NotImplementedError, 'carry on here'


class TimerTest(unittest.TestCase):

    def test_start(self):
        """Check we can start the timer"""
        timer = landiallerd.Timer()
        timer.start()
        try:
            real_time = landiallerd.time
            landiallerd.time = MockTime((39 * 60) + 23)
            self.assertEqual(timer.get_elapsed_time(), '00:39:23')
        finally:
            landiallerd.time = real_time

    def test_reset(self):
        """Check we can reset the timer"""
        timer = landiallerd.Timer()
        timer.start()
        try:
            real_time = landiallerd.time
            landiallerd.time = MockTime((39 * 60) + 23)
            timer.reset()
            self.assertEqual(timer.get_elapsed_time(), '00:00:00')
        finally:
            landiallerd.time = real_time

    def test_stop(self):
        """Check we can stop the timer"""
        timer = landiallerd.Timer()
        timer.start()
        try:
            real_time = landiallerd.time
            landiallerd.time = MockTime((39 * 60) + 23)
            timer.stop()
            self.assertEqual(timer.get_elapsed_time(), '00:39:23')
            landiallerd.time = MockTime((45 * 60) + 32)
            self.assertEqual(timer.get_elapsed_time(), '00:39:23')
        finally:
            landiallerd.time = real_time
            

if __name__ == '__main__':
    unittest.main()
