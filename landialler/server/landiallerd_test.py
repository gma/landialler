# $Id$


import mock
import time
import unittest
import threading
import xmlrpclib

import landiallerd


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

    def test_timer_stopped_by_default(self):
        """Check timer is stopped by default"""
        timer = landiallerd.Timer()
        self.assertEqual(timer.is_running, False)


class MockConfigParser:

    value = 'value from config file'

    def get(self, section, option):
        return self.value
    

class ModemTest(unittest.TestCase):

    SUCCESSFUL_COMMAND = 'ls / > /dev/null'
    FAILING_COMMAND = 'ls /missing.file.234324324 2> /dev/null'

    def setUp(self):
        self.config = MockConfigParser()

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
        """Check the timer is stopped when we hang up"""
        self.config.value = self.SUCCESSFUL_COMMAND
        modem = landiallerd.Modem(self.config)
        modem.dial()
        modem.is_connected()
        self.assertEqual(modem.timer.is_running, True)
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

    def test_timer_started_when_online(self):
        """Check the timer is only started when we're connected"""
        self.config.value = self.FAILING_COMMAND
        modem = landiallerd.Modem(self.config)
        modem.is_connected()
        try:
            real_time = landiallerd.time
            landiallerd.time = MockTime(18)
            self.assertEqual(modem.timer.elapsed_seconds, 0)
        finally:
            landiallerd.time = real_time
        

class MockTimer:

    elapsed_seconds = 14


class ModemProxyTest(unittest.TestCase):

    def test_dial_called_once(self):
        """Check the modem's dial() method is only called once"""
        modem = mock.Mock()
        proxy = landiallerd.ModemProxy(modem)
        proxy.add_client('client-id-1')
        proxy.add_client('client-id-2')
        self.assertEqual(len(modem.getNamedCalls('dial')), 1)

    def test_dont_dial_if_connected(self):
        """Check proxy doesn't dial up if modem connected"""
        modem = mock.Mock({'is_connected': True})
        proxy = landiallerd.ModemProxy(modem)
        proxy.add_client('client-id-1')
        self.assertEqual(len(modem.getNamedCalls('dial')), 0)

    def test_dial_return_code(self):
        """Check the proxied return code of modem's dial() method"""
        modem = mock.Mock({'dial': False, 'is_connected': False})
        proxy = landiallerd.ModemProxy(modem)
        self.assertEqual(proxy.add_client('client-id-1'), False)
        self.assertEqual(len(modem.getNamedCalls('dial')), 1)
        self.assertEqual(proxy.add_client('client-id-2'), False)
        self.assertEqual(len(modem.getNamedCalls('dial')), 1)

        modem = mock.Mock({'dial': True})
        proxy = landiallerd.ModemProxy(modem)
        self.assertEqual(proxy.add_client('client-id-1'), True)

        modem = mock.Mock({'dial': True, 'is_connected': True})
        proxy = landiallerd.ModemProxy(modem)
        self.assertEqual(proxy.add_client('client-id-1'), True)
        self.assertEqual(proxy.add_client('client-id-2'), True)

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
        proxy.add_client('client-id-1')
        proxy.add_client('client-id-2')
        proxy.add_client('client-id-2')
        self.assertEqual(proxy.count_clients(), 2)

        proxy.remove_client('client-id-1')
        self.assertEqual(proxy.count_clients(), 1)
        proxy.remove_client('client-id-2')
        self.assertEqual(proxy.count_clients(), 0)

        proxy.remove_client('bad-client-id')  # mustn't raise

    def test_automatic_hang_up(self):
        """Check modem hung up when no clients remain"""
        modem = mock.Mock({'is_connected': True})
        proxy = landiallerd.ModemProxy(modem)

        proxy.add_client('client-id-1')
        self.assertEqual(len(modem.getNamedCalls('is_connected')), 1)

        proxy.remove_client('client-id-1')
        self.assertEqual(len(modem.getNamedCalls('is_connected')), 2)
        self.assertEqual(len(modem.getNamedCalls('hang_up')), 1)

    def test_force_hangup(self):
        """Check the proxy can forcefully drop modem connection"""
        modem = mock.Mock({'is_connected': True})
        proxy = landiallerd.ModemProxy(modem)

        proxy.add_client('client-id-1')
        proxy.add_client('client-id-2')

        proxy.remove_client('client-id-1')
        proxy.hang_up()
        self.assertEqual(len(modem.getNamedCalls('hang_up')), 1)

    def test_hang_up_return_code(self):
        """Check the proxied return code of the modem's hang_up() method"""
        modem = mock.Mock({'is_connected': True, 'hang_up': True})
        proxy = landiallerd.ModemProxy(modem)
        self.assertEqual(proxy.hang_up(), True)

        modem = mock.Mock({'is_connected': True, 'hang_up': False})
        proxy = landiallerd.ModemProxy(modem)
        self.assertEqual(proxy.hang_up(), False)

    def test_timer(self):
        """Check the proxy can return time spent online"""
        timer = MockTimer()
        modem = landiallerd.Modem(MockConfigParser())
        modem.timer = timer
        proxy = landiallerd.ModemProxy(modem)
        self.assertEqual(proxy.get_time_connected(), 14)

    def test_forget_old_clients(self):
        """Check the proxy forgets about old clients"""
        modem = mock.Mock()
        proxy = landiallerd.ModemProxy(modem)
        proxy.add_client('client-id-1')
        self.assertEqual(proxy.count_clients(), 1)
        try:
            real_time = landiallerd.time
            offset = landiallerd.ModemProxy.CLIENT_TIMEOUT
            landiallerd.time = MockTime(offset)
            proxy.remove_old_clients()
            self.assertEqual(proxy.count_clients(), 0)
        finally:
            landiallerd.time = real_time

    def test_forgetting_drops_connection(self):
        """Check forgetting the last client drops the connection"""
        modem = mock.Mock({'is_connected': True})
        proxy = landiallerd.ModemProxy(modem)
        proxy.add_client('client-id-1')
        try:
            real_time = landiallerd.time
            offset = landiallerd.ModemProxy.CLIENT_TIMEOUT
            landiallerd.time = MockTime(offset)
            proxy.remove_old_clients()
            self.assertEqual(proxy.count_clients(), 0)
            hang_up_calls = modem.getNamedCalls('hang_up')
            self.assertEqual(len(hang_up_calls), 1)
        finally:
            landiallerd.time = real_time
        
    def test_refresh_client(self):
        """Check refreshing a client updates time client was last seen"""
        modem = mock.Mock()
        proxy = landiallerd.ModemProxy(modem)
        proxy.add_client('client-id-1')
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


class APITest(unittest.TestCase):

    def test_connect_when_connected(self):
        """Check the connect() returns True when connected"""
        modem = mock.Mock({'is_connected': True})
        proxy = landiallerd.ModemProxy(modem)
        api = landiallerd.API(proxy)
        self.assertEqual(api.connect('client-id-1'), xmlrpclib.True)
        self.assertEqual(proxy.count_clients(), 1)
        
    def test_connect_when_not_connected(self):
        """Check the connect() return code when not connected"""
        modem = mock.Mock({'is_connected': False, 'dial': False})
        proxy = landiallerd.ModemProxy(modem)
        api = landiallerd.API(proxy)
        self.assertEqual(api.connect('client-id-1'), xmlrpclib.False)

        modem = mock.Mock({'is_connected': False, 'dial': True})
        proxy = landiallerd.ModemProxy(modem)
        api = landiallerd.API(proxy)
        self.assertEqual(api.connect('client-id-1'), xmlrpclib.True)

    def test_disconnect_when_connected(self):
        """Check the disconnect() return code when connected"""
        modem = mock.Mock({'is_connected': True, 'hang_up': True})
        proxy = landiallerd.ModemProxy(modem)
        api = landiallerd.API(proxy)
        api.connect('client-id-1')
        self.assertEqual(proxy.count_clients(), 1)
        self.assertEqual(api.disconnect('client-id-1'), xmlrpclib.True)
        self.assertEqual(proxy.count_clients(), 0)

        modem = mock.Mock({'is_connected': True, 'hang_up': False})
        proxy = landiallerd.ModemProxy(modem)
        api = landiallerd.API(proxy)
        api.connect('client-id-1')
        self.assertEqual(proxy.count_clients(), 1)
        self.assertEqual(api.disconnect('client-id-1'), xmlrpclib.False)
        self.assertEqual(proxy.count_clients(), 0)

    def test_disconnect_not_connected(self):
        """Check the disconnect() return code when not connected"""
        modem = mock.Mock({'is_connected': False})
        proxy = landiallerd.ModemProxy(modem)
        api = landiallerd.API(proxy)
        self.assertEqual(api.disconnect('client-id-1'), xmlrpclib.True)

    def test_disconnect_all_users(self):
        """Check disconnect() can drop the connection for everybody"""
        modem = mock.Mock({'is_connected': True})
        proxy = landiallerd.ModemProxy(modem)
        api = landiallerd.API(proxy)
        api.connect('client-id-1')
        api.connect('client-id-2')
        api.connect('client-id-3')
        api.disconnect('client-id-1')
        self.assertEqual(len(modem.getNamedCalls('hang_up')), 0)
        api.disconnect('client-id-2', all=True)
        self.assertEqual(len(modem.getNamedCalls('hang_up')), 1)

    def test_client_refresh(self):
        """Check get_status() refreshes client"""
        modem = mock.Mock({'is_connected': True})
        modem.timer = MockTimer()
        proxy = landiallerd.ModemProxy(modem)
        api = landiallerd.API(proxy)
        api.connect('client-id-1')
        try:
            real_time = landiallerd.time
            offset = landiallerd.ModemProxy.CLIENT_TIMEOUT - 1
            landiallerd.time = MockTime(offset)
            api.get_status('client-id-1')
            offset = landiallerd.ModemProxy.CLIENT_TIMEOUT + 1
            landiallerd.time = MockTime(offset)
            self.assertEqual(proxy.count_clients(), 1)
        finally:
            landiallerd.time = real_time

    def test_get_num_clients(self):
        """Check get_status() returns number of clients"""
        modem = mock.Mock({'is_connected': True})
        modem.timer = MockTimer()
        proxy = landiallerd.ModemProxy(modem)
        proxy.add_client('client-id-1')
        proxy.add_client('client-id-2')
        proxy.add_client('client-id-3')
        api = landiallerd.API(proxy)
        self.assertEqual(api.get_status('client-id-1')[0], 3)

    def test_get_connection_status(self):
        """Check get_status() returns connection status"""
        modem = mock.Mock({'is_connected': True})
        modem.timer = MockTimer()
        proxy = landiallerd.ModemProxy(modem)
        api = landiallerd.API(proxy)
        self.assertEqual(api.get_status('client-id-1')[1], xmlrpclib.True)

        modem = mock.Mock({'is_connected': False})
        modem.timer = MockTimer()
        proxy = landiallerd.ModemProxy(modem)
        api = landiallerd.API(proxy)
        self.assertEqual(api.get_status('client-id-1')[1], xmlrpclib.False)
        
    def test_get_time_online(self):
        """Check get_status() returns time online"""
        modem = mock.Mock()
        modem.timer = MockTimer()
        proxy = landiallerd.ModemProxy(modem)
        api = landiallerd.API(proxy)
        api.connect('client-id-1')
        self.assertEqual(api.get_status('client-id-1')[2], 14)


class AutoDisconnecThreadTest(unittest.TestCase):

    def tearDown(self):
        for thread in threading.enumerate():
            if 'AutoDisconnect' in thread.getName():
                thread.join()

    def let_thread_work(self):
        time.sleep(0.01)

    def test_connection_dropped_no_users(self):
        """Check connection automatically dropped when there are no users"""
        modem = mock.Mock({'is_connected': True})
        proxy = landiallerd.ModemProxy(modem)
        thread = landiallerd.AutoDisconnectThread(proxy)
        thread.start()
        self.let_thread_work()
        thread.finished.set()
        self.assert_(len(modem.getNamedCalls('hang_up')) > 0)

    def test_connection_not_dropped_with_users(self):
        """Check connection not dropped when there are active users"""
        modem = mock.Mock({'is_connected': True})
        proxy = landiallerd.ModemProxy(modem)
        proxy.add_client('client-id')
        thread = landiallerd.AutoDisconnectThread(proxy)
        thread.start()
        self.let_thread_work()
        thread.finished.set()
        self.assertEqual(len(modem.getNamedCalls('hang_up')), 0)

    def test_thread_runs_continually(self):
        """Check the auto disconnect thread runs continually"""
        modem = mock.Mock({'is_connected': True})
        proxy = landiallerd.ModemProxy(modem)
        proxy.add_client('client-id')
        thread = landiallerd.AutoDisconnectThread(proxy)
        thread.start()
        self.let_thread_work()
        thread.finished.set()
        self.assert_(len(modem.getNamedCalls('is_connected')) > 0)

    def test_daemon_thread(self):
        """Check the auto disconnect thread is a daemon thread"""
        modem = mock.Mock()
        proxy = landiallerd.ModemProxy(modem)
        thread = landiallerd.AutoDisconnectThread(proxy)
        self.assert_(thread.isDaemon())
        thread.finished.set()
        
    def test_old_clients_removed(self):
        """Check the thread causes old clients to be removed"""
        modem = mock.Mock()
        proxy = landiallerd.ModemProxy(modem)
        proxy.add_client('client-1')
        self.assertEqual(proxy.count_clients(), 1)
        try:
            real_time = landiallerd.time
            landiallerd.time = MockTime(63)
            thread = landiallerd.AutoDisconnectThread(proxy)
            thread.start()
            self.let_thread_work()
            thread.finished.set()
            self.assertEqual(proxy.count_clients(), 0)
        finally:
            landiallerd.time = real_time
        

if __name__ == '__main__':
    unittest.main()
