#!/usr/bin/env python
#
# setup.py - landialler setup/install script
#
# Usage: python setup.py install
#
# $Id$

from distutils.core import setup

setup(name="landialler",
      version="0.2pre1",
      description="LANdialler client",
      author="Graham Ashton",
      author_email="ashtong@users.sourceforge.net",
      url="http://landialler.sourceforge.net/",
      packages=['landialler'],
      scripts=['landialler.py'])
