#!/usr/bin/env python
#
# landialler.py - the LAN dialler client
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

import ConfigParser
import gmalib
import os
import posixpath
import socket
import sys
import time
import Tkinter
import tkMessageBox as tkMBox
import xmlrpclib


class UserInterface(gmalib.Logger):
    def __init__(self):
        """Sets up the GUI toolkit.

        Calls the base class's initialisor, then creates (and then
        hides) the root Tk window.

        """
        gmalib.Logger.__init__(self)

        # hide main Tk window (which isn't used)
        root = Tkinter.Tk()
        root.withdraw()

    def showerror(self, text):
        """Display an error dialog with an OK button.

        The caption is set to "LANdialler: Error". The body of the
        error message is specified by text. An error message is also
        written with Logger.log_err().

        """
        self.log_err(text)
        tkMBox.showerror("Error", text)

    def showinfo(self, caption, text):
        """Display an info dialog with an OK button."""
        tkMBox.showinfo(caption, text)

    def askretrycancel(self, text):
        """Display a dialog with a question and retry/cancel buttons.

        Return 1 if retry is clicked, 0 if cancel is clicked.

        """
        return tkMBox.askretrycancel("Retry?", text)

    def askyesno(self, caption, text):
        """Ask if an operation should proceed.

        Displays a dialog with Yes and No buttons. The question is
        specified by text. The dialog's caption is "Landialler: caption".

        Returns 1 if the user presses the Yes button, 0 otherwise.

        """
        return tkMBox.askyesno(caption, text)


class App(gmalib.Application):
    def __init__(self):
        """Calls the base class's initialisor, initialises user interface."""

        gmalib.Application.__init__(self)
        self.ui = UserInterface()

    def main(self):
        """The main method, defining the landialler flow control.

        Begins by reading the landialler.conf configuration file. Then
        connects to the XML-RPC server (as specified in the config
        file).

        Then it calls the need_to_go_online() and go_online() methods
        to control the server's dial up connection.

        """

        try:
            # load config file
            self.config = ConfigParser.ConfigParser()
            self.config.read("landialler.conf")
            hostname = self.config.get("xmlrpcserver", "hostname")
            port = int(self.config.get("xmlrpcserver", "port"))

            # connect to the XML-RPC server
            self.client = xmlrpclib.Server("http://%s:%d/" % (hostname, port))
            self.log_info("connected to %s:%d" % (hostname, port))

            if self.need_to_go_online() == 0:
                sys.exit()

            success = 0
            while success == 0:  # keep trying until successful or user cancels
                success = self.go_online()
                if success:
                    # next dialog should have disconnect button (not OK),
                    # and be minimisable
                    self.ui.showinfo("Connected", "Click OK to disconnect")
                    print "closing connection"
                    self.client.disconnect()
                else:
                    if self.ui.askretrycancel("Connection timed out") == 0:
                        break  # user clicked cancel

        except socket.error, e:
            self.log_err("Error %d: %s" % (e.args[0], e.args[1]))
            if e.args[0] == 111:  # connection refused
                self.ui.showerror("Sorry, I couldn't connect to the " + \
                                  "landialler server. Is it turned on?")
            else:
                self.ui.showerror("%d: %s" % (e.args[0], e.args[1]))

    def need_to_go_online(self):
        """Determines whether we need to initiate a dial up connection.

        Asks the user to confirm that they wish to go online. If they
        do, and the server is not already dialled up, returns 1.
        Otherwise returns 0.

        """
        go_online = self.ui.askyesno("Go online?",
                                     "Would you like to go online?")
        if go_online:
            response = self.client.is_connected()  # is the server dialled up?
            if response.value == 1:
                self.ui.showinfo("Connected", "You are already online")
            else:
                return 1

        return 0

    def go_online(self):
        """Instructs the server to start the dial up connection.

        Initiaties the dial up connection by calling the XML-RPC
        connect() method. Waits up to "timeout" seconds for the
        connection to come up, checking the connection status with the
        XML-RPC is_connected() method every 5 seconds. The timeout
        parameter must be set in the landialler.conf configuration
        file, and defaults to 120 seconds.

        Returns 1 if the connection comes up inside timeout secs,
        0 otherwise.

        """
        
        self.log_info("starting connection")
        self.client.connect()

        online = 0        # are we online?
        paused = 0        # seconds waited for so far
        timeout = int(self.config.get("dialup", "timeout"))

        response = self.client.is_connected()
        while (response.value != 1) and (paused <= timeout):
            time.sleep(5)
            paused += 5
            print "checking connection (%d secs)" % paused
            response = self.client.is_connected()
            if response.value == 1:
                break

        if response.value == 0:  # timed out before we got online
            self.log_info("cancelling connection attempt")
            self.client.disconnect()

        return response.value


if __name__ == '__main__':
    app = App()
    app.debug = 1
    app.main()
