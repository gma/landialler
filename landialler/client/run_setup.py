#!/usr/bin/env python
# $Id$


"""LANdialler client setup script

Usage: python setup.py install

"""


class Installer(object):

    name = "landialler-client"

    classifiers = [
        "Development Status :: 4 - Beta",
        "Environment :: Win32 (MS Windows)",
        "Environment :: X11 Applications :: GTK",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Natural Language :: English",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX",
        "Programming Language :: Python",
        "Topic :: Internet",
        "Topic :: System :: Networking",
        "Topic :: Utilities"
        ]
    
    long_description = """\
    LANdialler allows workstations (Windows, Linux, etc.) on a LAN to
    control and share a modem attached to a Linux server. It is
    designed to be used with PPP and NAT on a Linux router to provide
    a home or small office with shared Internet access."""

    def get_data_files(self):
        import os
        if os.name == "posix":
            conf_dir = "etc"
            filename = ".prefix"  # created by setup.py
            if os.path.exists(filename):
                prefix = file(filename).read()
                if prefix == "/usr":
                    conf_dir = "/%s" % conf_dir
                os.remove(".prefix")
            return [("share/landialler/glade", ["landialler.glade"]),
                    (conf_dir, ["landialler.conf"])]
        else:
            return []

    def install(self):
        import distutils.core
        import landialler
        distutils.core.setup(
            name=self.name,
            version=landialler.__version__,
            description="LANdialler client program",
            long_description=self.long_description,
            author="Graham Ashton",
            author_email="ashtong@users.sourceforge.net",
            url="http://landialler.sourceforge.net/",
            license="GPL",
            classifiers=self.classifiers,
            scripts=["landialler"],
            data_files=self.get_data_files()
            )


installer = Installer()
installer.install()


#     if sys.argv[1] <> 'install':
#         sys.exit(0)   # Only continue if we're doing an "install"

#     # Copy stuff into /usr/local if we're on a POSIX system.
#     if os.name == 'posix':
#         bin_dir = '/usr/local/bin'
#         bin_file = 'landialler.py'
#         glade_file = 'landialler.glade'
#         conf_dir = '/usr/local/etc'
#         conf_file = 'landialler.conf'

#         # install landialler.py, landialler.glade
#         print 'copying %s, %s to %s' % (bin_file, glade_file, bin_dir)
#         if (not os.path.exists(bin_dir)) or (not os.path.isdir(bin_dir)):
#             error_msg('%s is not a directory' % bin_dir)
#         shutil.copyfile(bin_file, os.path.join(bin_dir, bin_file))
#         os.chmod('%s/%s' % (bin_dir, bin_file), 0755)
#         shutil.copyfile(glade_file, os.path.join(bin_dir, glade_file))

#         # install landialler.conf
#         print 'copying %s to %s' % (conf_file, conf_dir)
#         if (not os.path.exists(conf_dir)) or (not os.path.isdir(conf_dir)):
#             error_msg('%s is not a directory' % conf_dir)
#         shutil.copyfile(conf_file, '%s/%s' % (conf_dir, conf_file))
#         os.chmod('%s/%s' % (conf_dir, conf_file), 0644)

#     # Tell windows users to do it themselves.
#     else:
#         print """
# Please copy landialler.py, landialler.glade and landialler.conf into
# the same directory (e.g. 'C:\Program Files\landialler' on Windows). Edit
# the landialler.conf file to point to your LANdialler server, and then
# run "python landialler.py" from a command prompt.

# If you would prefer to run LANdialler without the command prompt
# window rename landialler.py to landialler.pyw and create a desktop
# shortcut that executes "python landialler.pyw" for you, but make sure
# that the shortcut starts in the landialler directory.
# """
