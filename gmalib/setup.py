#!/usr/bin/env python
#
# setup.py - gmalib setup/install script
#
# Usage: python setup.py install
#
# $Id$


import distutils.core

import gmalib


if __name__ == '__main__':
    distutils.core.setup(name="gmalib",
                         version=gmalib.__version__,
                         description="used by author's own applications",
                         author="Graham Ashton",
                         author_email="ashtong@users.sourceforge.net",
                         url="http://landialler.sourceforge.net/",
                         py_modules=['gmalib'])
