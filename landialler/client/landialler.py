#!/usr/bin/env python
#
# landialler.py - the LAN dialler client
#
# Connects to a landiallerd daemon on a local server/router and
# controls the dial up link from a client workstation.
#
# $Id$

import application
import ConfigParser
import os
import posixpath
import socket
import sys
import syslog
import Tkinter
import tkMessageBox as dialog
import xmlrpclib


class App(application.Application):
    def __init__(self):
        self.debug = 1

    def connect(self):
        """Ask the server to connect to dial up.

        Calls the XML-RPC connect() procedure, asking the server to
        configure it's Internet link.

        """

        response = self.client.connect()

    def is_connected(self):
        """Checks to see if we're online or not.

        Returns 1 if we are online, 0 if not.

        """

        response = self.client.is_connected()
        if response.value == 1:
            return 1
        else:
            return 0


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
            dialog.showerror("Error", msg)
            sys.exit()
    
    def run(self):
        if os.name == "posix":
            syslog.openlog(posixpath.basename(sys.argv[0]),
                           syslog.LOG_PID | syslog.LOG_CONS)

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

            if self.is_connected():
                dialog.showinfo("Already Online", "You are already online!")
                sys.exit()
            else:
                dial_up = dialog.askyesno("Go online?",
                                          "Would you like to go online?")

        except socket.error, e:
            self.log_err("Error %d: %s" % (e.args[0], e.args[1]))
            if e.args[0] == 111:  # connection refused
                msg = "Sorry, I couldn't connect to the landialler server. " + \
                      "Is it turned on?"
                dialog.showerror("Error", msg)
            else:
                dialog.showerror("Error",
                                 "Error %d: %s" % (e.args[0], e.args[1]))

##         except Exception, e:
##             self.log_err("Untrapped error: %s" % e)

        if os.name == "posix":
            syslog.closelog()


if __name__ == '__main__':
    app = App()
    app.run()
