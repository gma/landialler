# $Id$


import mock
import time
import unittest
# import xmlrpclib

import landiallerd


# class SharedModemTest:

#     def test_remember_client(self):
#         """Check we can remember a client"""
#         modem = landiallerd.SharedModem(MockConfigParser())
#         modem.remember_client('127.0.0.1')
#         self.assertEqual(modem.count_clients(), 1)
#         modem.remember_client('127.0.0.1')
#         self.assertEqual(modem.count_clients(), 1)
#         modem.remember_client('127.0.0.2')
#         self.assertEqual(modem.count_clients(), 2)

#     def test_forget_client(self):
#         """Check we can forget clients"""
#         modem = landiallerd.SharedModem(MockConfigParser())
#         modem.remember_client('127.0.0.1')
#         modem.remember_client('127.0.0.2')
#         modem.remember_client('127.0.0.3')
#         self.assertEqual(modem.count_clients(), 3)
#         modem.forget_client('127.0.0.2')
#         self.assertEqual(modem.count_clients(), 2)
#         modem.forget_all_clients()
#         self.assertEqual(modem.count_clients(), 0)

#     def test_list_clients(self):
#         """Check we can list all clients"""
#         modem = landiallerd.SharedModem(MockConfigParser())
#         ip1 = '127.0.0.1'
#         ip2 = '127.0.0.2'
#         modem.remember_client(ip1)
#         modem.remember_client(ip2)
#         clients = modem.list_clients()
#         clients.sort()
#         self.assertEqual(clients, [ip1, ip2])

#     def test_forget_old_clients(self):
#         """Check that old clients are forgotten about automatically"""
#         modem = landiallerd.SharedModem(MockConfigParser())
#         modem.remember_client('127.0.0.1')
#         real_time, landiallerd.time = landiallerd.time, MockTime(3600)
#         try:
#             self.assertEqual(modem.count_clients(), 1)
#             modem.forget_old_clients()
#             self.assertEqual(modem.count_clients(), 0)
#         finally:
#             landiallerd.time = real_time        

#     def test_connect_command(self):
#         """Check that we test the return value of the connect command"""
#         modem = landiallerd.SharedModem(MockConfigParser())
#         mock_os = MockOsModule()
#         real_os, landiallerd.os = landiallerd.os, mock_os
#         try:
#             mock_os.rval = 0
#             rval = modem.dial()
#             self.assertEqual(rval, True)

#             mock_os.rval = 1
#             rval = modem.dial()
#             self.assertEqual(rval, False)
#         finally:
#             landiallerd.os = real_os


# class APITest:

#     def test_connect_when_connected(self):
#         """Check the API's connect procedure when connected"""
#         modem = Mock({'is_connected': True})
#         api = landiallerd.API(modem)
#         self.assertEqual(api.connect('127.0.0.1'), xmlrpclib.True)

#     def test_connect_when_connecting(self):
#         """Check the API's connect procedure when connecting"""
#         modem = Mock(None,
#                      {'is_connected': False,
#                       'is_connecting': True})
#         api = landiallerd.API(modem)
#         self.assertEqual(api.connect('127.0.0.1'), xmlrpclib.False)
        
#     def test_connect_when_disconnected(self):
#         """Check the API's connect procedure when not connected"""
#         modem = Mock({'dial': True},
#                      {'is_connected': False})
#         api = landiallerd.API(modem)
#         self.assertEqual(api.connect('127.0.0.1'), xmlrpclib.True)

#         modem = Mock({'dial': False},
#                      {'is_connected': False})
#         api = landiallerd.API(modem)
#         self.assertEqual(api.connect('127.0.0.1'), xmlrpclib.False)

#     def test_disconnect_not_connected(self):
#         """Check the API's disconnect procedure when not connected"""
#         modem = Mock({'hangup': True},
#                      {'is_connected': False})
#         api = landiallerd.API(modem)
#         self.assertEqual(api.disconnect('127.0.0.1'), xmlrpclib.True)
#         # TODO: write client tracker (test first) and split it out of
#         # modem


class MockTime:

    def __init__(self, offset):
        self._offset = offset

    def time(self):
        return time.time() + self._offset


class TimerTest(unittest.TestCase):

    def test_start(self):
        """Check we can start the timer"""
        timer = landiallerd.Timer()
        timer.start()
        try:
            real_time = landiallerd.time
            offset = (39 * 60) + 23
            landiallerd.time = MockTime(offset)
            self.assertEqual(timer.elapsed_seconds, offset)
        finally:
            landiallerd.time = real_time

    def test_reset(self):
        """Check we can reset the timer"""
        timer = landiallerd.Timer()
        timer.start()
        try:
            real_time = landiallerd.time
            offset = (39 * 60) + 23
            landiallerd.time = MockTime(offset)
            timer.reset()
            self.assertEqual(timer.elapsed_seconds, 0)
        finally:
            landiallerd.time = real_time

    def test_stop(self):
        """Check we can stop the timer"""
        timer = landiallerd.Timer()
        timer.start()
        try:
            real_time = landiallerd.time
            offset = (39 * 60) + 23
            landiallerd.time = MockTime(offset)
            timer.stop()
            self.assertEqual(timer.elapsed_seconds, offset)
            landiallerd.time = MockTime((45 * 60) + 32)
            self.assertEqual(timer.elapsed_seconds, offset)
        finally:
            landiallerd.time = real_time

    def test_elapsed_seconds(self):
        """Check we can keep track of elapsed seconds"""
        timer = landiallerd.Timer()
        timer.start()
        try:
            real_time = landiallerd.time
            landiallerd.time = MockTime((10 * 60) + 23)
            timer.stop()
            self.assertEqual(timer.elapsed_seconds, 623)
        finally:
            landiallerd.time = real_time


class MockConfigParser:

    value = 'value from config file'

    def get(self, section, option):
        return self.value
    

class MockConfigTest(unittest.TestCase):

    SUCCESSFUL_COMMAND = 'ls / > /dev/null'
    FAILING_COMMAND = 'ls /missing.file.234324324 2> /dev/null'

    def setUp(self):
        self.config = MockConfigParser()


class ModemTest(MockConfigTest):

    def test_dial(self):
        """Check we can dial the modem and receive the return code"""
        self.config.value = self.SUCCESSFUL_COMMAND
        modem = landiallerd.Modem(self.config)
        self.assertEqual(modem.dial(), True)

        self.config.value = self.FAILING_COMMAND
        modem = landiallerd.Modem(self.config)
        self.assertEqual(modem.dial(), False)

    def test_hang_up(self):
        """Check we can hang up the modem and receive the return code"""
        self.config.value = self.SUCCESSFUL_COMMAND
        modem = landiallerd.Modem(self.config)
        self.assertEqual(modem.hang_up(), True)

        self.config.value = self.FAILING_COMMAND
        modem = landiallerd.Modem(self.config)
        self.assertEqual(modem.hang_up(), False)

    def test_is_connected(self):
        """Check we can test if we're connected"""
        self.config.value = self.SUCCESSFUL_COMMAND
        modem = landiallerd.Modem(self.config)
        self.assertEqual(modem.is_connected(), True)

        self.config.value = self.FAILING_COMMAND
        modem = landiallerd.Modem(self.config)
        self.assertEqual(modem.is_connected(), False)

    def test_timer(self):
        """Check the timer is only running when modem known to be connected"""
        self.config.value = self.SUCCESSFUL_COMMAND
        modem = landiallerd.Modem(self.config)
        modem.dial()
        modem.is_connected()
        try:
            real_time = landiallerd.time
            offset = (39 * 60) + 23
            landiallerd.time = MockTime(offset)
            modem.is_connected()
            self.assertEqual(modem.timer.elapsed_seconds, offset)
            modem.hang_up()
            landiallerd.time = MockTime(offset + 1)
            self.assertEqual(modem.timer.elapsed_seconds, offset)
            modem.dial()
            self.assertEqual(modem.timer.elapsed_seconds, 0)
        finally:
            landiallerd.time = real_time


class ModemProxyTest(unittest.TestCase):

    def test_dial_called_once(self):
        """Check the modem's dial() method is only called once"""
        modem = mock.Mock()
        proxy = landiallerd.ModemProxy(modem)
        proxy.dial('client-id-1')
        proxy.dial('client-id-2')
        self.assertEqual(len(modem.getNamedCalls('dial')), 1)
        self.assertEqual(len(modem.getAllCalls()), 1)

    def test_dial_return_code(self):
        """Check the proxied return code of modem's dial() method"""
        modem = mock.Mock({'dial': False})
        proxy = landiallerd.ModemProxy(modem)
        self.assertEqual(proxy.dial('client-id-1'), False)

        modem = mock.Mock({'dial': True})
        proxy = landiallerd.ModemProxy(modem)
        self.assertEqual(proxy.dial('client-id-1'), True)

    def test_is_connected(self):
        """Check proxy knows when we're connected"""
        modem = mock.Mock({'is_connected': True})
        proxy = landiallerd.ModemProxy(modem)
        self.assert_(proxy.is_connected())

        modem = mock.Mock({'is_connected': False})
        proxy = landiallerd.ModemProxy(modem)
        self.failIf(proxy.is_connected())

    def test_client_counting(self):
        """Check proxy keeps track of number of connected clients"""
        modem = mock.Mock({'is_connected': True})
        proxy = landiallerd.ModemProxy(modem)
        proxy.dial('client-id-1')
        proxy.dial('client-id-2')
        self.assertEqual(proxy.count_clients(), 2)

        proxy.hang_up('client-id-1')
        self.assertEqual(proxy.count_clients(), 1)
        proxy.hang_up('client-id-2')
        self.assertEqual(proxy.count_clients(), 0)

        proxy.hang_up('bad-client-id')  # mustn't raise

    def test_automatic_hang_up(self):
        """Check modem hung up when no clients remain"""
        modem = mock.Mock({'is_connected': True})
        proxy = landiallerd.ModemProxy(modem)

        proxy.dial('client-id-1')
        proxy.hang_up('client-id-1')

        connected_calls = modem.getNamedCalls('is_connected')
        self.assertEqual(len(connected_calls), 1)
        hang_up_calls = modem.getNamedCalls('hang_up')
        self.assertEqual(len(hang_up_calls), 1)

    def test_force_hangup(self):
        """Check the proxy can hang up all clients"""
        modem = mock.Mock({'is_connected': True})
        proxy = landiallerd.ModemProxy(modem)

        proxy.dial('client-id-1')
        proxy.dial('client-id-2')
        proxy.hang_up('client-id-1', all=True)

        connected_calls = modem.getNamedCalls('is_connected')
        self.assertEqual(len(connected_calls), 1)
        hang_up_calls = modem.getNamedCalls('hang_up')
        self.assertEqual(len(hang_up_calls), 1)

    def test_timer(self):
        """Check the proxy can return time spent online"""

        class Timer:

            pass

        timer = Timer()
        timer.elapsed_seconds = 14
        modem = landiallerd.Modem(MockConfigParser())
        modem.timer = timer
        proxy = landiallerd.ModemProxy(modem)
        self.assertEqual(proxy.get_time_connected(), 14)

    def test_forget_old_clients(self):
        """Check the proxy forgets about old clients"""
        modem = mock.Mock()
        proxy = landiallerd.ModemProxy(modem)
        proxy.dial('client-id-1')
        self.assertEqual(proxy.count_clients(), 1)
        try:
            real_time = landiallerd.time
            offset = landiallerd.ModemProxy.CLIENT_TIMEOUT
            landiallerd.time = MockTime(offset)
            self.assertEqual(proxy.count_clients(), 0)
        finally:
            landiallerd.time = real_time

    def test_forgetting_drops_connection(self):
        """Check forgetting the last client drops the connection"""
        modem = mock.Mock({'is_connected': True})
        proxy = landiallerd.ModemProxy(modem)
        proxy.dial('client-id-1')
        try:
            real_time = landiallerd.time
            offset = landiallerd.ModemProxy.CLIENT_TIMEOUT
            landiallerd.time = MockTime(offset)
            proxy.count_clients()
            hang_up_calls = modem.getNamedCalls('hang_up')
            self.assertEqual(len(hang_up_calls), 1)
        finally:
            landiallerd.time = real_time
        
    def test_refresh_client(self):
        """Check refreshing a client updates time client was last seen"""
        modem = mock.Mock()
        proxy = landiallerd.ModemProxy(modem)
        proxy.dial('client-id-1')
        try:
            real_time = landiallerd.time
            offset = landiallerd.ModemProxy.CLIENT_TIMEOUT
            landiallerd.time = MockTime(offset)
            proxy.refresh_client('client-id-1')
            self.assertEqual(proxy.count_clients(), 1)
            hang_up_calls = modem.getNamedCalls('hang_up')
            self.assertEqual(len(hang_up_calls), 0)
        finally:
            landiallerd.time = real_time


if __name__ == '__main__':
    unittest.main()
