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
import tkMessageBox as dialog
import xmlrpclib


class App(gmalib.Application):
    def __init__(self):
        self.debug = 1

    def read_config(self):
        """Map config file settings to instance attributes.

        This really ought to be sorted out so that load_sys_config()
        can do everything for us. Making a mental note to fix the
        library...

        """
        
        self.sys_config_files = ["/usr/local/etc/landialler.conf",
                                 "c:\landialler\landialler.conf",
                                 "%s/landialler.conf" % os.getcwd()]
        self.load_sys_config()

        try:
            self.server_host = self.config.get("server", "hostname")
            self.server_port = self.config.get("server", "port")

        except ConfigParser.NoOptionError, e:
            msg = "Error reading config file: %s" % e
            self.log_err(msg)
            dialog.showerror("Landialler: Error", msg)
            sys.exit()
    
    def run(self):
        root = Tkinter.Tk()
        root.withdraw()

        try:
            # load config file data into attributes
            self.read_config()

            # connect to the server and attempt to dial up if necessary
            self.client = xmlrpclib.Server("http://%s:%s/" %
                                           (self.server_host, self.server_port))
            self.log_debug("connected to %s:%s" % (self.server_host,
                                                   self.server_port))

            response = self.client.is_connected()
            if response.value == 1:
                dialog.showinfo("Landialler: already online",
                                "You are already online")
                sys.exit()
            else:
                go_online = dialog.askyesno("Landialler: go online?",
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
                        dialog.showinfo("Landialler: connected!",
                                        "You are now online")
                        break
                    else:
                        time.sleep(5)
                        paused += 5

                # The next OK button shouldn't be clicked until we're
                # ready to disconnect from the Internet.
                
                if response.value == 1:
                    dialog.showinfo("Landialler: disconnect?",
                                    "Click OK to disconnect")
                print "closing connection"
                self.client.disconnect()

                # Now sit in a loop while attempting to disconnect,
                # checking the status as we go; not as clean as it
                # could be but it'll do as a first implementation.
                
                paused = 0
                response = self.client.is_connected()
                while (response.value == 1) and (paused < max_pause):
                    time.sleep(5)
                    paused += 5
                    print "checking connection (%d secs)" % paused
                    response = self.client.is_connected()
                if response.value == 1:
                    dialog.showerror("Landialler: error",
                                     "Error: Unable to disconnect. " + \
                                     "You are probably still online.")
                sys.exit()

        except socket.error, e:
            self.log_err("Error %d: %s" % (e.args[0], e.args[1]))
            if e.args[0] == 111:  # connection refused
                msg = "Sorry, I couldn't connect to the landialler server. " + \
                      "Is it turned on?"
                dialog.showerror("Landialler: error", msg)
            else:
                dialog.showerror("Landialler: error",
                                 "Error %d: %s" % (e.args[0], e.args[1]))

##         except Exception, e:
##             self.log_err("Untrapped error: %s" % e)


if __name__ == '__main__':
    app = App()
    app.run()
