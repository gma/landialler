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

    def _advance_clock(self, seconds):

        class MockTime:

            def time(self):
                return time.time() + seconds
            
        self._real_time, landiallerd.time = landiallerd.time, MockTime()

    def _reset_clock(self):
        landiallerd.time = self._real_time        

    def test_forget_old_clients(self):
        """Check that old clients are forgotten about automatically"""
        self.conn.remember_client('127.0.0.1')
        self._advance_clock(3600)
        self.conn.forget_old_clients()
        self._reset_clock()
        self.assertEqual(self.conn.count_clients(), 0)

    def test_connect_command(self):
        """Check that we test the return value of the connect command"""

        class MockOsModule:

            rval = None
            
            def system(self, *args):
                return self.rval

        mock_os = MockOsModule()
        real_os, landiallerd.os = landiallerd.os, mock_os

        mock_os.rval = 0
        rval = self.conn.run_connect_command()
        self.assertEqual(rval, True)

        mock_os.rval = 1
        rval = self.conn.run_connect_command()
        self.assertEqual(rval, False)
        

if __name__ == '__main__':
    unittest.main()
