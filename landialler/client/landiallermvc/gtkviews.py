#!/usr/bin/env python
#
# gtkviews.py - GTK+ interface for the LANdialler client
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


"""implements the GTK+ landialler user interface

Most classes in this file are GTK+ specific sub classes of those in
views.py that define the MVC views. Where this is not the case they
are present simply to aid the GTK+ implementation. Please see views.py
for more documentation, especially for many of the methods, whose
purpose is only documented in views.py.

"""


from gtk import *
import views


main_win = None  # global variable so the Dialog class can refer to it too


class Window:

    def __init__(self):
        self.window = None
        self.window_type = WINDOW_TOPLEVEL
        self.window = GtkWindow(self.window_type)

    def draw(self):
        self.window.set_border_width(1)
        self.window.set_title(self.title)
        self.window.set_policy(0, 0, 0)  # fix window size
        hbox = GtkHBox()
        self.vbox = GtkVBox()
        hbox.pack_start(self.vbox, expand=1, fill=1, padding=6)
        self.window.add(hbox)

    def add_button_box(self):
        """Lays out a set of buttons in a button bar."""
        bbox = GtkHButtonBox()
        bbox.set_layout(BUTTONBOX_END)
        bbox.set_spacing(6)
        self.create_button_store()
        self.button_bar.reverse()
        for tup in self.button_bar:
            (name, pos, callback) = tup
            button = GtkButton(name)
            button.connect("clicked", callback)
            bbox.pack_end(button)
            key = name
            self.button_store[key] = button  # so we can configure it
        self.vbox.pack_start(bbox, expand=1, fill=1, padding=6)

    def start_event_loop(self):
        mainloop()


class Dialog(Window):

    def __init__(self):
        Window.__init__(self)
        self.window_type = WINDOW_DIALOG

    def draw(self):
        """Displays the dialog's message and buttons."""
        Window.draw(self)
        global main_win
        if main_win:
            self.window.set_transient_for(main_win)
        if self.modal:
            self.window.set_modal(1)
        self.add_label()
        self.add_separator()
        self.add_button_box()
        self.window.show_all()
    
    def add_label(self):
        label = GtkLabel(self.text)
        label.set_padding(6, 0)
        self.vbox.pack_start(label, expand=1, fill=1, padding=8)
    
    def add_separator(self):
        seperator = GtkHSeparator()
        self.vbox.pack_start(seperator, expand=1, fill=1, padding=6)


class ConnectingDialog(Dialog, views.ConnectingDialog):

    def __init__(self, model):
        Dialog.__init__(self)
        views.ConnectingDialog.__init__(self, model)

    def cleanup(self):
        mainquit()
    
    def update(self):
        if self.model.is_connected:
            self.window.destroy()


class DisconnectDialog(Dialog, views.DisconnectDialog):

    def __init__(self, model):
        Dialog.__init__(self)
        views.DisconnectDialog.__init__(self, model)
    
    def cleanup(self):
        mainquit()


class DroppedDialog(Dialog, views.DroppedDialog):

    def __init__(self, model):
        Dialog.__init__(self)
        views.DroppedDialog.__init__(self, model)
    
    def cleanup(self):
        mainquit()
    
    def update(self):
        if self.model.is_connected:
            self.window.destroy()
            self.model.detach(self)


class FatalErrorDialog(Dialog, views.FatalErrorDialog):

    def __init__(self, model, **kwargs):
        Dialog.__init__(self)
        views.FatalErrorDialog.__init__(self, model, **kwargs)
    
    def cleanup(self):
        mainquit()
    

class MainWindow(Window, views.MainWindow):

    def __init__(self, model):
        Window.__init__(self)
        views.MainWindow.__init__(self, model)
        global main_win
        main_win = self.window
        
        # GtkLabels that need updating from the update() method must be
        # stored somewhere so that we can get at them.
        self.status_label = {"is_connected": None, "current_users": None}

    def check_status(self):
        self.model.get_server_status()
        return 1

    def cleanup(self):
        mainquit()
    
    def draw(self):
        """Display the main window."""
        Window.draw(self)
        self.window.connect("destroy", mainquit)
        self.add_status_frame()
        self.add_button_box()
        self.update()
        self.window.show_all()

    def add_status_frame(self):
        """Draws frame containing status display."""
        frame = GtkFrame()
        frame.set_shadow_type(SHADOW_ETCHED_IN)
        table = GtkTable(rows=2, cols=2, homogeneous=0)
        table.set_row_spacings(4)
        table.set_col_spacings(10)
        table.set_border_width(5)
        
        i = 0
        for row in self.status_rows:
            (col1, col2) = row
            label1 = GtkLabel(str(col1))
            label1.set_alignment(0, 0.5)
            table.attach(label1, 0, 1, i, i+1)
            label2 = GtkLabel(str(col2))
            label2.set_alignment(1, 0.5)
            if i == 0:
                self.status_label["is_connected"] = label2
            elif i == 1:
                self.status_label["current_users"] = label2
            else:
                raise NotImplementedError, "too many status rows"
            table.attach(label2, 1, 2, i, i+1)
            i += 1

        frame.add(table)        
        self.vbox.pack_start(frame, expand=1, fill=1, padding=6)

    def start_event_loop(self):
        timeout_add(self.model.check_status_period, self.check_status)
        Window.start_event_loop(self)

    def update(self):
        users_label = self.status_label["current_users"]
        status_label = self.status_label["is_connected"]
        
        users_label.set_text(str(self.model.current_users))
        if self.model.is_connected:
            status_label.set_text("Online")
            #self.button_store["Disconnect"].set_state(STATE_NORMAL)
        else:
            status_label.set_text('Offline')
            #self.button_store["Disconnect"].set_state(STATE_INSENSITIVE)

        if (not self.model.is_connected) and self.model.was_connected:
            self.model.was_connected = 0
            dialog = DroppedDialog(self.model)
            dialog.draw()
