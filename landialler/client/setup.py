#!/usr/bin/env python
# $Id$


import distutils.core
import distutils.sysconfig
import os
import shutil
import sys


def get_prefix():
    dist = distutils.core.run_setup('run_setup.py',
                                    script_args=sys.argv[1:],
                                    stop_after='commandline')
    default_prefix = distutils.sysconfig.get_config_var('prefix')
    try:
        return dist.get_option_dict('install')['prefix'][1]
    except LookupError:
        return default_prefix


def create_script(prefix):
    shutil.copyfile("landialler.py", "landialler")
    script = "landialler"
    # modify path to glade file
    file = "landialler.glade"
    abspath = os.path.join(prefix, "share/landialler/glade", file)
    os.system("perl -p -i -e 's|%s|%s|' %s" % (file, abspath, script))

    # modify path to config file
    file = "landialler.conf"
    if prefix == "/usr":
        prefix = "/"
    print 'joining', (prefix, "etc", file)
    abspath = os.path.join(prefix, "etc", file)
    os.system("perl -p -i -e 's|%s|%s|' %s" % (file, abspath, script))


if __name__ == "__main__":
    prefix = get_prefix()
    create_script(prefix)
    file(".prefix", "w").write(prefix)
    dist = distutils.core.run_setup('run_setup.py', script_args=sys.argv[1:])
