#!/usr/bin/env python
#
# landialler.py - the landialler client
#
# Copyright (C) 2001-2004 Graham Ashton
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


"""set up a shared network connection (via the server)

LANdialler enables several computers on a home LAN to remotely control
a dial up device (e.g. modem) that is connected to a single Unix
workstation. This scenario is explained in more detail on the
LANdialler web site.

There are two programs that make up a complete LANdialler system; the
client (landialler) and the server (landiallerd). You're reading the
documentation for the client.

When you run landialler.py it contacts the server and determines if it
is currently connected (e.g. dialled up). If so, the client registers
itself with the server as a new client and the user is informed that
they are currently online. Otherwise the client asks the server to
connect, displaying feedback to the user confirming that the server is
currently connecting.

Once the server reports that the connection is made, the client
displays the number of users that are currently using the
connection. The user has the option to disconnect at any time. If
there are other users online then the user can choose to either either
unregister themselves (thereby allowing the server to disconnect when
all users have unregistered), or to forceably terminate the
connection, disconnecting all other users at the same time.

If the connection drops out at any time (let's face it, it can happen
a lot with modems) a dialog box pops up alerting the user, after which
landialler.py exits (at some point in the future there may be an
option for the user to attempt to reconnect instead).

All client-server communication takes place via the LANdialler XML-RPC
API, which is covered in landiallerd.py's documentation.

The configuration file tells landialler how to contact the server. A
sample configuration file looks like this:

  [xmlrpcserver]
  hostname: 192.168.1.1  # your Unix box
  port: 6543             # the default port

The configuration file should be called "landialler.conf". On POSIX
operating systems (e.g. Unix or similar) it can either be placed in
/usr/local/etc, or the current directory. On other operating systems
it must be placed in the current directory.

On POSIX operating systems error, informational and debugging messages
are written to syslog.

More information on LANdialler is available at the project home page:

  http://landialler.sourceforge.net/

The author can be contacted at ashtong@users.sourceforge.net.

"""


# # For more information on the Model-View-Controller design pattern,
# # see http://www.ootips.org/mvc-pattern.html


# import exceptions
# import ConfigParser
# import getopt
# import landiallermvc
# from landiallermvc import Model
# import os
# import socket
# import sys
# import xmlrpclib


# __version__ = "0.2.1"


# class Dummy:

#     def method(self, *args):
#         pass
    
#     def __getattr__(self, name):
#         return self.method

# # TODO: replace with proper logging object
# log = Dummy()


# class App:

#     def __init__(self):
#         """Calls the base class's initialisor."""
#         self.conf_file = None
#         self.debug = 0
#         self.toolkit = None
    
#     def getopt(self):
#         """Parse command line arguments.
        
#         Reads the command line arguments, looking for the following:
        
#         -c file      path to configuration file
#         -d           enable debugging for extra output
#         -h	     display this message on stderr
#         -u toolkit   select user interface toolkit (tk or gtk)
        
#         """
#         opts, args = getopt.getopt(sys.argv[1:], "c:dhu:")
        
#         for o, v in opts:
#             if o == "-c":
#                 self.conf_file = v
#             elif o == "-d":
#                 self.debug = 1
#             elif o == "-h":
#                 self.usage_message()
#             elif o == "-u":
#                 self.toolkit = v

#     def handle_connect_error(self):
#         log.err("Error: ConnectError")
#         msg = "There was a problem\nconnecting to the network."
#         dialog = self.model.views.FatalErrorDialog(self.model, message=msg)
#         dialog.draw()
#         dialog.start_event_loop()

#     def handle_disconnect_error(self):
#         log.err("Error: DisconnectError")
#         msg = "There was a problem disconnecting\nfrom the network. " + \
#               "You may not have\nbeen disconnected properly!"
#         dialog = self.model.views.FatalErrorDialog(self.model, message=msg)
#         dialog.draw()
#         dialog.start_event_loop()

#     def handle_socket_error(self, e):
#         log.err("Error: socket error: %s (%d)" % (e.args[1], e.args[0]))
#         msg = "Unable to connect to server: %s" % e.args[1]
#         log.err(msg)
#         dialog = self.model.views.FatalErrorDialog(self.model, message=msg)
#         dialog.draw()
#         dialog.start_event_loop()

#     def handle_status_error(self):
#         log.err("Error: StatusError")
#         msg = "LANdialler is unable to determine the\nstatus of your " + \
#               "network connection.\n\nPlease check the connection and\n" + \
#               "the server and try again."
#         dialog = self.model.views.FatalErrorDialog(self.model, message=msg)
#         dialog.draw()
#         dialog.start_event_loop()

#     def handle_error(self, e):
#         log.err("Error: %s" % e)
#         msg = "Error: %s" % e
#         dialog = self.model.views.FatalErrorDialog(self.model, message=msg)
#         dialog.draw()
#         dialog.start_event_loop()

#     def main(self):
#         """The main method, runs the application.
        
#         Begins by reading the landialler.conf configuration file. Then
#         connects to the XML-RPC server (as specified in the config
#         file).
        
#         Initialises and launches the user interface.
        
#         """
#         try:
#             # read command line options and config file
#             self.getopt()
#             config = ConfigParser.ConfigParser()
#             if self.conf_file:
#                 if not os.path.exists(self.conf_file):
#                     raise IOError, "File not found: %s" % self.conf_file
#                 else:
#                     config.read(self.conf_file)
#             else:
#                 files = []
#                 if os.name == "posix":
#                     files.append("/usr/local/etc/landialler.conf")
#                 files.append("landialler.conf")
#                 config.read(files)
        
#             # run the core of the application
#             hostname = config.get("xmlrpcserver", "hostname")
#             port = config.get("xmlrpcserver", "port")
        
#             server = xmlrpclib.Server("http://%s:%s/" % (hostname, port))
#             log.debug("connected to %s:%s" % (hostname, port))
#             self.model = Model.Model(config, server, self.toolkit)
#             window = self.model.views.MainWindow(self.model)

#         except getopt.GetoptError, e:
#             sys.stderr.write("%s\n" % e)
#             self.usage_message()

#         except SystemExit:  # ignore calls to sys.exit()
#             raise

#         except Exception, e:
#             sys.stderr.write("%s\n" % e)
#             sys.exit(1)
        
#         # from now on we can do GUI based error messages
#         try:
#             window.draw()
#             self.model.get_server_status()
#             if not self.model.is_connected:
#                 dialog = self.model.views.ConnectingDialog(self.model)
#                 dialog.draw()
#                 self.model.server_connect()
#             window.start_event_loop()
        
#         except landiallermvc.ConnectError:
#             self.handle_connect_error()
#         except landiallermvc.DisconnectError:
#             self.handle_disconnect_error()
#         except landiallermvc.StatusError:
#             self.handle_status_error()
#         except socket.error, e:
#             self.handle_socket_error(e)
#         except Exception, e:
#             self.handle_error(e)

#     def usage_message(self):
#         """Print usage message to sys.stderr and exit."""
#         message = """usage: %s [-d] [-f] [-h] [-l file] [-s]

# Options:

#     -c file     path to configuration file
#     -d          enable debugging for extra output
#     -h	        display this message on stderr
#     -u toolkit  select user interface toolkit (tk or gtk)

# """ % os.path.basename(sys.argv[0])
#         sys.stderr.write(message)
#         sys.exit(1)


import os
import socket
import time

import pygtk; pygtk.require('2.0')
import gtk
import gtk.glade


class TestServer:

    def get_status(self, foo):
        return 1, True, time.time()


class RemoteModem:

    def __init__(self, server_proxy):
        self._server_proxy = server_proxy

    def _get_client_id(self):
        ip = socket.gethostbyname(socket.gethostname())
        try:
            return '%s@%s' % (os.environ['USER'], ip)
        except KeyError:
            return ip

    client_id = property(_get_client_id)

    def dial(self):
        return self._server_proxy.dial(self.client_id)

    def hang_up(self):
        return self._server_proxy.hang_up(self.client_id)

    def get_status(self):
        return self._server_proxy.get_status(self.client_id)


class WidgetWrapper:

    def __init__(self, root_widget):
        self._root_widget_name = root_widget
        self._xml = gtk.glade.XML('landialler.glade', root_widget)
        self._connect_signals()

    def _get_root_widget(self):
        return getattr(self, self._root_widget_name)

    root_widget = property(_get_root_widget)

    def __getattr__(self, name):
        widget = self._xml.get_widget(name)
        if widget is None:
            raise AttributeError, name
        return widget
    
    def _connect_signals(self):
        for name in self.__class__.__dict__.keys():
            if hasattr(self, name):
                candidate_callback = getattr(self, name)
                if callable(candidate_callback):
                    self._xml.signal_connect(name, candidate_callback)


class Window(WidgetWrapper):

    def show(self):
        self.root_widget.show()

    def destroy(self):
        self.root_widget.destroy()


class MainWindow(Window):

    CHECK_PERIOD = 1000 * 10  # 10 seconds
    STATUS_LABEL = '<span size="larger" weight="bold">You are %s</span>'

    def __init__(self, modem):
        Window.__init__(self, 'main_window')
        self._modem = modem
        self._set_status_disconnected()
        gtk.timeout_add(self.CHECK_PERIOD, self._check_status)

    def _check_status(self):
        users, connected, seconds_connected = self._modem.get_status()
        if connected:
            self._set_status_connected(users, seconds_connected)
        else:
            self._set_status_disconnected()
        return gtk.TRUE
            
    def _set_status(self, status):
        self.status_label.set_label(self.STATUS_LABEL % status)

    def _set_status_connected(self, users, seconds_connected):
        self._set_status('connected')
        time_str = time.strftime('%H:%M:%S', time.gmtime(seconds_connected))
        user_str = { True: 'user', False: 'users' }[users == 1]
        self.details_label.set_label('%s %s, %s' % (users, user_str, time_str))
        self.connect_button.set_sensitive(gtk.FALSE)
        self.disconnect_button.set_sensitive(gtk.TRUE)

    def _set_status_disconnected(self):
        self._set_status('disconnected')
        self.connect_button.set_sensitive(gtk.TRUE)
        self.disconnect_button.set_sensitive(gtk.FALSE)

    def on_main_window_delete_event(self, *args):
        self._modem.hang_up()
        gtk.main_quit()

    def on_connect_button_clicked(self, *args):
        dialog = ConnectingDialog()
        dialog.show()

    def on_disconnect_button_clicked(self, *args):
        dialog = DisconnectDialog()
        dialog.show()


class ConnectingDialog(Window):

    def __init__(self):
        Window.__init__(self, 'connecting_dialog')
        self._start_progress_bar()

    def _start_progress_bar(self):

        def pulse():
            try:
                self.progressbar1.pulse()
                return gtk.TRUE
            except AttributeError:
                return gtk.FALSE
        
        gtk.timeout_add(100, pulse)

    def on_cancel_button_clicked(self, *args):
        self.destroy()

    def on_connecting_dialog_delete_event(self, *args):
        self.on_cancel_button_clicked()


class DisconnectDialog(Window):

    def __init__(self):
        Window.__init__(self, 'disconnect_dialog')


class App:

    def main(self):
        try:
            modem = RemoteModem(TestServer())
            window = MainWindow(modem)
            window.show()
            gtk.main()
        except KeyboardInterrupt:
            modem.hang_up()
            gtk.main_quit()


if __name__ == "__main__":
    app = App()
    app.main()
        

if __name__ == "__main__":
    app = App()
    app.main()
