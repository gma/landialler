#!/usr/bin/env python
#
# tkviews.py - Tk interface for the landialler client
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


"""implements the Tk landialler user interface

Most classes in this file are undocumented, bacause they are simply Tk
specific sub classes of the classes in views.py that define the MVC
views. Where this is not the case they are present simply to aid the
Tk implementation, and are briefly documented to explain their
purpose.

"""


from Tkinter import *
import views


root = Tk()  # Instantiated explicitly so that we can access it later.
             # Also means that we don't get a spare top level window
             # floating around if we create a dialog before drawing
             # the main window.


class Window(views.Window):
    def __init__(self):
        views.Window.__init__(self)
        self.button_side = RIGHT  # right aline buttons

    def draw_buttons(self, parent=None):
        self.create_button_store()
        frame = Frame(parent, bd=6)  # padding frame
        count = 0
        for tuple in self.button_bar:
            (name, pos, cmd) = tuple
            button = Button(frame, text=name.capitalize(), command=cmd)
            key = name.lower()
            self.button_store[key] = button  # so we can call btn.config()

            if count % 2: padding = 6
            else:         padding = 0
            button.pack(side=self.button_side, padx=padding)
            count += 1

        frame.pack(side=self.button_side)


class Dialog(Window):

    """Simple class for creating generic dialog boxes."""

    def __init__(self):
        """Set default button_side attribute to TOP."""
        Window.__init__(self)
        self.modal = 0
        self.window = None

    def draw(self):
        """Displays the dialog's message and buttons."""
        self.window = Toplevel()
        self.window.title(self.title)
        self.window.protocol('WM_DELETE_WINDOW', lambda: 0)  # ignore close
        frame = Frame(self.window, bd=6)
        max_cols = 15
        max_pixels = 160
        if len(self.text) > max_cols:
            widget = Message(frame, text=self.text, width=max_pixels)
        else:
            widget = Label(frame, text=self.text, width=len(self.text))
        widget.pack()
        frame.pack()
        self.draw_buttons(self.window)
        self.window.focus_set()
        if self.modal:
            self.window.grab_set()
            self.window.wait_window()


class ConnectingDialog(Dialog, views.ConnectingDialog):
    def __init__(self, model):
        Dialog.__init__(self)
        views.ConnectingDialog.__init__(self, model)

    def cleanup(self):
        """Cleans up after the dialog has been closed."""
        global root
        self.window.destroy()
        root.quit()

    def update(self):
        """Closes the dialog once the connection is made."""
        if self.model.is_connected:
            self.window.destroy()
    

class DisconnectDialog(Dialog, views.DisconnectDialog):
    def __init__(self, model):
        Dialog.__init__(self)
        views.DisconnectDialog.__init__(self, model)
        self.modal = 1

    def cleanup(self):
        """Cleans up after the Yes or No buttons have been pressed.

        Destroys the dialog box.

        """
        self.window.destroy()

    def update(self):
        """Do nothing."""
        pass


class DroppedDialog(Dialog, views.DroppedDialog):
    def __init__(self, model):
        Dialog.__init__(self)
        views.DroppedDialog.__init__(self, model)
        self.modal = 1

    def cleanup(self):
        """Cleans up after the OK button has been pressed.

        Exits the application.

        """
        global root
        self.window.destroy()
        root.quit()

    def update(self):
        """Do nothing."""
        pass


class MainWindow(Window, views.MainWindow):
    def __init__(self, model):
        Window.__init__(self)
        views.MainWindow.__init__(self, model)
        self.default_var = []  # stores variable values (i.e. actual status)
        self.update_var = []   # StringVar() object's for auto label updating
        for row in self.status_rows:
            (label, value) = row
            self.default_var.append(value)
            self.update_var.append(StringVar())

    def cleanup(self):
        """Destroy the main window."""
        global root
        root.quit()

    def draw(self):
        """Display the main window."""
        global root
        root.title(self.title)
        on_delete_cb = self.buttons['disconnect'][1]  # same as disconnect btn
        root.protocol('WM_DELETE_WINDOW', on_delete_cb)
        self.draw_labels()
        self.draw_buttons()
        self.status_check()
        self.update()  # update labels immediately
        mainloop()

    def draw_labels(self, parent=None):
        """Draws frame containing status display."""
        frame1 = Frame(parent, bd=6)                 # padding frame
        frame2 = Frame(frame1, bd=2, relief=GROOVE)  # layout frame

        row = 0
        for tuple in self.status_rows:
            (label, value) = tuple
            widget = Label(frame2, text=label)
            widget.grid(row=row, sticky=W, padx=2, pady=2)

            var = StringVar()
            var.set(self.default_var[row])
            self.update_var[row] = var
            widget = Label(frame2, textvariable=var)
            widget.grid(row=row, col=1, sticky=E, padx=2, pady=2)
            row += 1

        frame2.pack()
        frame1.pack()

    def status_check(self):
        """Regularly check the connection status on the server.

        Calls the model's get_server_status() method every
        status_check_period milliseconds.

        """
        global root
        self.model.get_server_status()
        root.after(self.model.status_check_period, self.status_check)  # re-run

    def update(self):
        """Updates the status display."""
        self.update_var[1].set(self.model.current_users)
        if self.model.is_connected:
            self.update_var[0].set('Online')
            self.button_store['disconnect'].config(state=ACTIVE)
        else:
            self.update_var[0].set('Offline')
            self.button_store['disconnect'].config(state=DISABLED)

        if (not self.model.is_connected) and self.model.was_connected:
            dialog = DroppedDialog(self.model)
            dialog.draw()
