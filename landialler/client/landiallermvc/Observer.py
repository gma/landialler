# views.py - abstract View class (see the MVC pattern)
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

"""implements abstract Observer class

In the Model-View-Controller design pattern View and Controller
components are both "observers" of the Model. The Observer design
pattern is a publish-subscribe mechanism by which the publisher (in
this case the model) notifies it's subscribers (i.e. the observers)
that data has changed and that they should retrieve it if they wish.

Observers register with the model when they are created, by calling
the model's attach() method. The model can then notify the observers
by running each observer's update() method when data is changed.

"""


class Observer:
    def __init__(self, model):
        """Register with the model's publish-subscribe mechanism."""
        self.model = model
        self.model.attach(self)  # observe the model

    def update(self):
        """Update the status data (abstract method).

        A view is an observer of the model. This method is called
        automatically by the model's publish-subscribe system. All
        views must override this method, even if it does nothing.

        """
        raise NotImplementedError, \
              ("%s has not implemented update()" % self.__class__)

