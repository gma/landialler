#!/usr/bin/env python
#
# swingviews.py - Java Swing interface for the LANdialler client
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


"""implements the Swing landialler user interface

Most classes in this file are Swing specific sub classes of those in
views.py that define the MVC views. Where this is not the case they
are present simply to aid the Swing implementation. Please see views.py
for more documentation, especially for many of the methods, whose
purpose is only documented in views.py.

You will need jython configured to run the Swing interface.

"""


from javax.swing import *
from java.awt import *
from java.awt.event import *
from javax.swing.border import *

import sys
import views


mainWindow = None  # global variable so the dialogs can refer to it too


class ConnectingDialog(views.ConnectingDialog):

    def __init__(self, model):
        views.ConnectingDialog.__init__(self, model)
        self.border = EmptyBorder(6, 6, 6, 6)
        self.dialog = None
        self.button = None

    def draw(self):
        global mainWindow

        self.dialog = JDialog(mainWindow, self.title)
        self.dialog.resizable = 0
        self.dialog.contentPane.layout = FlowLayout()

        fullPanel = JPanel()  # for padding round the dialog edge
        fullPanel.border = self.border
        fullPanel.layout = BoxLayout(fullPanel, BoxLayout.Y_AXIS)
        self.dialog.contentPane.add(fullPanel)

        self.addLabel(fullPanel)
        self.addSeparator(fullPanel)
        self.addButton(fullPanel)
        self.registerMouseHandler()

        self.dialog.pack()
        self.dialog.setVisible(1)

    def addLabel(self, parent):
        panel = JPanel()
        panel.border = EmptyBorder(0, 0, 10, 0)
        label = JLabel(self.text)
        panel.add(label)
        parent.add(panel)

    def addSeparator(self, parent):
        separator = JSeparator()
        parent.add(separator)
        
    def addButton(self, parent):
        button = JButton("Cancel")
        panel = JPanel()
        panel.layout = BorderLayout()
        panel.border = EmptyBorder(10, 0, 0, 0)
        panel.add(button, BorderLayout.EAST)
        parent.add(panel)
        self.button = button
        
    def registerMouseHandler(self):

        class MouseHandler(MouseAdapter):
            def __init__(self, callback):
                self.callback = callback
                
            def mouseClicked(self, event):
                self.callback()

        callback = self.buttons["Cancel"][1]
        self.button.mouseListener = MouseHandler(callback)

    def cleanup(self):
        pass
##         sys.exit()

    def update(self):
        if self.model.is_connected:
            self.dialog.visible = 0
            self.dialog.dispose()


class MainWindow(views.MainWindow):

    def __init__(self, model):
        views.MainWindow.__init__(self, model)
        self.border = EmptyBorder(6, 6, 6, 6)

    def check_status(self):
        self.model.get_server_status()
        return 1

    def cleanup(self):
        pass
    
    def draw(self):
        """Display the main window."""
        global mainWindow
        frame = JFrame(self.title)
        frame.resizable = 0
        mainWindow = frame
        frame.contentPane.setLayout(BoxLayout(frame.contentPane, 1))

        frame.contentPane.add(self.getStatusPanel())
        frame.contentPane.add(self.getBottomPanel())
        self.registerMouseHandler()

        frame.pack()
        frame.setVisible(1)

    def getStatusPanel(self):
        panel = JPanel()
        panel.border = CompoundBorder(self.border, EtchedBorder())
        panel.layout = BoxLayout(panel, 0)
        panel.add(self.getLeftPanel())
        panel.add(self.getRightPanel())
        return panel

    def getLeftPanel(self):
        panel = JPanel()
        panel.border = self.border
        panel.layout = BoxLayout(panel, 1)

        panel.add(JLabel(self.status_rows[0][0]))
        panel.add(JLabel(self.status_rows[1][0]))
        return panel

    def getRightPanel(self):
        panel = JPanel()
        panel.border = self.border
        self.statusValue = JLabel(self.status_rows[0][1])
        self.usersValue = JLabel(self.status_rows[1][1])
        self.statusValue.alignmentX = 1  # right aligned
        self.usersValue.alignmentX = 1
        panel.layout = BoxLayout(panel, 1)
        panel.add(self.statusValue)
        panel.add(self.usersValue)
        return panel

    def getBottomPanel(self):
        panel = JPanel()
        panel.layout = BorderLayout()
        self.button = JButton("Disconnect")
        panel.add(self.button, BorderLayout.EAST)
        panel.border = self.border
        return panel

    def registerMouseHandler(self):

        class MouseHandler(MouseAdapter):
            def __init__(self, callback):
                self.callback = callback
                
            def mouseClicked(self, event):
                self.callback()

        callback = self.buttons["Disconnect"][1]
        self.button.mouseListener = MouseHandler(callback)

    def start_event_loop(self):

        class ActionHandler(ActionListener):

            def __init__(self, callback):
                self.callback = callback

            def actionPerformed(self, event):
                self.callback()

        ah = ActionHandler(self.check_status)
        timer = Timer(self.model.check_status_period, ah)
        timer.repeats = 1
        timer.start()

    def update(self):
        pass
