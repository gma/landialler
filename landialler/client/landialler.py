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
a lot with modems) a dialog box pops up alerting the user.

The configuration file tells landialler how to contact the server. A
sample configuration file looks like this:

  [server]
  hostname: 192.168.1.1  # your Unix box
  port: 6543             # the default port

The configuration file should be called "landialler.conf". On POSIX
operating systems (e.g. Unix or similar) it can either be placed in
/usr/local/etc, or the current directory. On other operating systems
it must be placed in the same directory as landialler.py.

More information on LANdialler is available at the project home page:

  http://landialler.sourceforge.net/

The author can be contacted at ashtong@users.sourceforge.net.

"""


import ConfigParser
import os
import socket
import sys
import time
import traceback
import xmlrpclib

import pygtk; pygtk.require('2.0')
import gtk
import gtk.glade


class Observable(object):

    def __init__(self):
        self._observers = {}

    def add_observer(self, observer):
        self._observers[observer] = None

    def remove_observer(self, observer):
        del self._observers[observer]

    def notify_observers(self):
        for observer in self._observers.keys():
            observer.update()


class RemoteModem(Observable):

    def __init__(self, server_proxy):
        Observable.__init__(self)
        self._server_proxy = server_proxy
        self._checking_status = False
        self.num_users = 0
        self.is_connected = False
        self.seconds_online = 0

    def _get_client_id(self):
        ip = socket.gethostbyname(socket.gethostname())
        try:
            return '%s@%s' % (os.environ['USER'], ip)
        except KeyError:
            return ip

    client_id = property(_get_client_id)

    def connect(self):
        self._server_proxy.connect(self.client_id)
        self._checking_status = True

    def disconnect(self):
        self._checking_status = False
        self.is_connected = False
        self.notify_observers()
        self._server_proxy.disconnect(self.client_id)

    def disconnect_all(self):
        # TODO: refactor into hang_up()
        self._checking_status = False
        self.is_connected = False
        self.notify_observers()
        self._server_proxy.disconnect(self.client_id, all=True)

    def get_status(self):
        if self._checking_status:
            self.num_users, self.is_connected, self.seconds_online = \
                            self._server_proxy.get_status(self.client_id)
        self.notify_observers()


class WidgetWrapper(object):

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

    CHECK_STATUS_PERIOD = 1000 * 2
    STATUS_LABEL = '<span size="larger" weight="bold">You are %s</span>'
    TITLE = 'LANdialler'
    UPDATE_TIMER_PERIOD = 100

    def __init__(self, modem):
        Window.__init__(self, 'main_window')
        self._modem = modem
        self._modem.add_observer(self)
        self._set_status_disconnected()
        self._seconds_online = 0
        self._last_check_time = None
        self._status_timeout = None
        gtk.timeout_add(self.UPDATE_TIMER_PERIOD, self._update_timer)
        self.connect()

    def update(self):
        self._last_check_time = time.time()
        if self._modem.is_connected:
            self._set_status_connected(self._modem.seconds_online)
        else:
            self._set_status_disconnected()
        return gtk.TRUE
            
    def _set_status_label(self, status):
        self.status_label.set_label(self.STATUS_LABEL % status)

    def _set_status_connected(self, seconds_online):
        self._set_status_label('connected')
        time_str = time.strftime('%H:%M:%S', time.gmtime(seconds_online))
        user_str = { True: 'user', False: 'users' }[self._modem.num_users == 1]
        self.details_label.set_label(
            '%s %s, online for %s' %
            (self._modem.num_users, user_str, time_str))
        self.root_widget.set_title('%s (connected)' % MainWindow.TITLE)
        self.connect_button.set_sensitive(gtk.FALSE)
        self.disconnect_button.set_sensitive(gtk.TRUE)

    def _update_timer(self):
        if self._modem.is_connected:
            secs_since_check = time.time() - self._last_check_time
            secs_online = self._modem.seconds_online + secs_since_check
            self._set_status_connected(secs_online)
        return True

    def _set_status_disconnected(self):
        self._set_status_label('disconnected')
        self.details_label.set_label('')
        self.root_widget.set_title(MainWindow.TITLE)
        self.connect_button.set_sensitive(gtk.TRUE)
        self.disconnect_button.set_sensitive(gtk.FALSE)

    def on_main_window_delete_event(self, *args):
        self._modem.remove_observer(self)
        try:
            if self._modem.is_connected:
                self._modem.disconnect()
        except socket.error:
            pass
        gtk.main_quit()

    def _check_status(self):
        self._modem.get_status()
        return gtk.TRUE

    def connect(self):
        if self._status_timeout:
            gtk.timeout_remove(self._status_timeout)
        self._status_timeout = gtk.timeout_add(
            self.CHECK_STATUS_PERIOD, self._check_status)
        self._modem.connect()
        dialog = ConnectingDialog(self._modem)
        dialog.show()

    def on_connect_button_clicked(self, *args):
        self.connect()

    def on_disconnect_button_clicked(self, *args):
        dialog = DisconnectDialog(self._modem)
        dialog.show()


class ConnectingDialog(Window):

    def __init__(self, modem):
        Window.__init__(self, 'connecting_dialog')
        self._modem = modem
        self._progress_timeout = None
        self._modem.add_observer(self)
        self._start_progress_bar()

    def _start_progress_bar(self):

        def pulse():
            self.progressbar1.pulse()
            return gtk.TRUE
        
        self._progress_timeout = gtk.timeout_add(100, pulse)

    def destroy(self):
        gtk.timeout_remove(self._progress_timeout)
        self._modem.remove_observer(self)
        Window.destroy(self)

    def update(self):
        if self._modem.is_connected:
            self.destroy()

    def on_cancel_button_clicked(self, *args):
        self._modem.disconnect()
        self.destroy()

    def on_connecting_dialog_delete_event(self, *args):
        self.on_cancel_button_clicked()


class DisconnectDialog(Window):

    def __init__(self, modem):
        Window.__init__(self, 'disconnect_dialog')
        self._modem = modem

    def on_disconnect_button_clicked(self, *args):
        if self.disconnect_all.get_active():
            self._modem.disconnect_all()
        else:
            self._modem.disconnect()
        self.destroy()

    def on_cancel_button_clicked(self, *args):
        self.destroy()

    def on_disconnect_dialog_delete_event(self, *args):
        self.on_cancel_button_clicked()


class ErrorDialog(Window):

    def __init__(self, primary_text, secondary_text):
        Window.__init__(self, 'error_dialog')
        self._primary_text = primary_text
        self._secondary_text = secondary_text

    def on_close_button_clicked(self, *args):
        self.destroy()

    def on_error_dialog_delete_event(self, *args):
        self.on_close_button_clicked()

    def show(self):
        label = self.label.get_label()
        self.label.set_label(label %
                             (self._primary_text, self._secondary_text))
        Window.show(self)


class ExceptionDialog(Window):

    def __init__(self, exc_text):
        Window.__init__(self, 'exception_dialog')
        buffer = self.textview1.get_buffer()
        buffer.set_text(exc_text)

    def on_details_button_clicked(self, *args):
        if self.scrolledwindow1.get_property('visible'):
            self.details_button.set_label('Details >>')
            self.scrolledwindow1.set_property('visible', gtk.FALSE)
        else:
            self.details_button.set_label('Details <<')
            self.scrolledwindow1.set_property('visible', gtk.TRUE)
        self.root_widget.queue_resize()

    def on_close_button_clicked(self, *args):
        self.destroy()

    def on_exception_dialog_delete_event(self, *args):
        self.on_close_button_clicked()


class ExceptionHandler:

    def __init__(self):
        sys.excepthook = self.handler

    def handler(self, exc_type, exc_value, exc_traceback):
        if isinstance(exc_value, socket.error):
            dialog = ErrorDialog(
                "Can't Contact Server",
                "The LANdialler server is not available. Please check "
                "that it is running, and that the server address is "
                "set correctly in the client configuration file.")
            dialog.show()
        else:
            exc_text = ''.join(traceback.format_tb(exc_traceback))
            dialog = ExceptionDialog(exc_text)
            dialog.show()

    
class App(object):

    def __init__(self):
        self._config = ConfigParser.ConfigParser()
        self._config.read('landialler.conf')

    def _connect_to_server(self):
        hostname = self._config.get('server', 'hostname')
        port = self._config.get('server', 'port')
        return xmlrpclib.ServerProxy('http://%s:%s/' % (hostname, port))
        
    def main(self):
        try:
            ExceptionHandler()
            server = self._connect_to_server()
            modem = RemoteModem(server)
            window = MainWindow(modem)
            window.show()
            gtk.main()
        except KeyboardInterrupt:
            modem.disconnect()
            gtk.main_quit()


if __name__ == "__main__":
    app = App()
    app.main()
