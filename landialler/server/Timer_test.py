#!/usr/bin/env python
#
# Timer_test.py - unit tests for the Timer class.
#
# Copyright (C) 2001 Graham Ashton
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
#
# $Id$


from landiallerd import Timer
import unittest


class TimerTestCase(unittest.TestCase):

    """Tests the Timer class."""

    def testElapsedTime(self):
        """Check elapsed seconds"""
        t = Timer()
        t.start()
        time.sleep(2)
        t.stop()
        self.assertEquals(t.getElapsedSeconds(), 2)


if __name__ == "__main__":
    unittest.main()
