# $Id$


import time
import unittest

import landiallerd


class MockConfigParser:

    value = 'value from config file'

    def read(self, files):
        print 'mock running'

    def get(self, section, option):
        return self.value
    

class MockTime:

    def __init__(self, advance_by):
        self._advance_by = advance_by

    def time(self):
        return time.time() + self._advance_by


class ConnectionTest(unittest.TestCase):

    def setUp(self):
        self._real_config_parser = landiallerd.gmalib.SharedConfigParser
        landiallerd.gmalib.SharedConfigParser = MockConfigParser

        landiallerd.Connection._shared_state = {}
        self.conn = landiallerd.Connection()

    def tearDown(self):
        landiallerd.gmalib.SharedConfigParser = self._real_config_parser
        
    def test_remember_client(self):
        """Check we can remember a client"""
        self.conn.remember_client('127.0.0.1')
        self.assertEqual(self.conn.count_clients(), 1)
        self.conn.remember_client('127.0.0.1')
        self.assertEqual(self.conn.count_clients(), 1)
        self.conn.remember_client('127.0.0.2')
        self.assertEqual(self.conn.count_clients(), 2)

    def test_forget_client(self):
        """Check we can forget clients"""
        self.conn.remember_client('127.0.0.1')
        self.conn.remember_client('127.0.0.2')
        self.conn.remember_client('127.0.0.3')
        self.assertEqual(self.conn.count_clients(), 3)
        self.conn.forget_client('127.0.0.2')
        self.assertEqual(self.conn.count_clients(), 2)
        self.conn.forget_all_clients()
        self.assertEqual(self.conn.count_clients(), 0)

    def test_list_clients(self):
        """Check we can list all clients"""
        ip1 = '127.0.0.1'
        ip2 = '127.0.0.2'
        self.conn.remember_client(ip1)
        self.conn.remember_client(ip2)
        clients = self.conn.list_clients()
        clients.sort()
        self.assertEqual(clients, [ip1, ip2])

    def test_forget_old_clients(self):
        """Check that old clients are forgotten about automatically"""
        self.conn.remember_client('127.0.0.1')
        real_time, landiallerd.time = landiallerd.time, MockTime(3600)
        try:
            self.assertEqual(self.conn.count_clients(), 1)
            self.conn.forget_old_clients()
            self.assertEqual(self.conn.count_clients(), 0)
        finally:
            landiallerd.time = real_time        

    def test_connect_command(self):
        """Check that we test the return value of the connect command"""

        class MockOsModule:

            rval = None
            
            def system(self, *args):
                return self.rval

        mock_os = MockOsModule()
        real_os, landiallerd.os = landiallerd.os, mock_os
        try:
            mock_os.rval = 0
            rval = self.conn.run_connect_command()
            self.assertEqual(rval, True)

            mock_os.rval = 1
            rval = self.conn.run_connect_command()
            self.assertEqual(rval, False)
        finally:
            landiallerd.os = real_os


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
