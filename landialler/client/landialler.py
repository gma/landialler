#!/usr/bin/env python
#
# landialler.py - the LAN dialler client
#
# Connects to a landiallerd daemon on a local server/router and
# controls the dial up link from a client workstation.
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
        tkMBox.showerror("LANdialler: Error", text)

    def showinfo(self, caption, text):
        """Display an info dialog with an OK button."""
        tkMBox.showinfo("LANdialler: %s" % caption, text)

    def askyesno(self, caption, text):
        """Ask if an operation should proceed.

        Displays a dialog with Yes and No buttons. The question is
        specified by text. The dialog's caption is "Landialler: caption".

        Returns 1 if the user presses the Yes button, 0 otherwise.

        """
        rval = tkMBox.askyesno("LANdialler: %s" % caption, text)
        return rval


class App(gmalib.Application):
    def __init__(self):
        """Calls the base class's initialisor."""

        gmalib.Application.__init__(self)

    def read_config(self):
        """Map config file settings to instance attributes.

        This really ought to be sorted out so that load_sys_config()
        can do everything for us. Making a mental note to fix the
        library...

        """
        self.sys_config_files = ["/usr/local/etc/landialler.conf",
                                 "c:\landialler\landialler.conf",
                                 os.getcwd() + os.sep + "landialler.conf"]
        self.load_sys_config()

        try:
            self.server_host = self.config.get("server", "hostname")
            self.server_port = self.config.get("server", "port")

        except ConfigParser.NoOptionError, e:
            self.ui.showerror("Error reading config file: %s" % e)
            sys.exit()
    
    def main(self):
        self.ui = UserInterface()

        try:
            # load config file data into attributes
            self.read_config()

            # connect to the server and attempt to dial up if necessary
            self.client = xmlrpclib.Server("http://%s:%s/" %
                                           (self.server_host, self.server_port))
            self.log_info("connected to %s:%s" % (self.server_host,
                                                   self.server_port))

            response = self.client.is_connected()
            if response.value == 1:
                self.ui.showinfo("Online", "You are already online")
                sys.exit()
            else:
                go_online = self.ui.askyesno("Go online?",
                                             "Would you like to go online?")
                if not go_online:
                    sys.exit()

                print "starting connection"
                self.client.connect()

                online = 0        # are we online?
                paused = 0        # seconds waited for so far
                max_pause = 120  # seconds to wait before giving up

                response = self.client.is_connected()
                while (response.value != 1) and (paused < max_pause):
                    print "checking connection (%d secs)" % paused
                    response = self.client.is_connected()
                    if response.value == 1:
                        self.ui.showinfo("connected!", "You are now online")
                        break
                    else:
                        time.sleep(5)
                        paused += 5

                # The next OK button shouldn't be clicked until we're
                # ready to disconnect from the Internet. It would be
                # better if it was a button labelled Disconnect, and
                # the dialog was minimisable. We really need to extend
                # the UserInterface class so that it can support
                # simple dialogs with an array of buttons...
                
                if response.value == 1:
                    self.ui.showinfo("Disconnect?", "Click OK to disconnect")
                    print "closing connection"
                    self.client.disconnect()
                else:
                    print "cancelling connection attempt"
                    self.client.disconnect()
                    # should be able to click retry here...
                    self.ui.showinfo("Timed out", "Sorry, connection timed out")

                # Now sit in a loop while attempting to disconnect,
                # checking the status as we go. Disconnecting should
                # be immediate, but we wait for it to timeout just in
                # case.
                
                paused = 0
                response = self.client.is_connected()
                while (response.value == 1) and (paused < max_pause):
                    time.sleep(5)
                    paused += 5
                    print "checking connection (%d secs)" % paused
                    response = self.client.is_connected()
                if response.value == 1:
                    self.ui.showerror("Unable to disconnect. " + \
                                      "You are probably still online.")
                sys.exit()

        except socket.error, e:
            self.log_err("Error %d: %s" % (e.args[0], e.args[1]))
            if e.args[0] == 111:  # connection refused
                self.ui.showerror("Sorry, I couldn't connect to the " + \
                                  "landialler server. Is it turned on?")
            else:
                self.ui.showerror("%d: %s" % (e.args[0], e.args[1]))


if __name__ == '__main__':
    app = App()
    app.debug = 1
    app.main()
