Ninja Sysop
===========

DON'T USE THIS ON PRODUCTION SYSTEM
===================================


Ninja sysop is web interface to configure system service after it has been deployed.

You can deploy your Dhcpd server with many vlans or listen interfaces as you need, and 
leave to users to auto-register his mac/ip assignement.

For DNS, you can deploy bind9 with many zones and offer to users a simple web tool to
manage some DNS records like A or CNAMEs entries.

It's use python pyramid web framework and twitter bootstrap for look & feel

Development Deploy
==================

Python 2.7 and virtualenv is required.


1. Download repository:

   `git clone git://github.com/ant30/ninja-sysop.git`

1. Create a virtualenv:

    `virtualenv ninja-sysop`

1. Load virtualenv:

    `cd ninja-sysop`

    `source bin/activate`

1. Deploy package as development:

    `python setup.py develop`

1. To run the development server execute:

    `pserve development.init --reload`

1. Go to http://localhost:6543 to get Web Interface


The default login is defined on examples/htpasswd as admin/admin, you can
create many users as you need with htpasswd utility from apache2-tools. If you
want add your own files you must edit development.init and modify ninjasysop
block like this:

    ninjasysop.backend = bind9
    ninjasysop.htpasswd = examples/htpasswd
    # name pathfile (multiline)
    ninjasysop.files =
        example.com:examples/bind9/db.example.com
    # name protected,names (multiline)
    ninjasysop.protected_names =
        example.com:mail,www,@

1. Set your backend according to the service you want configure.
1. Set your own htpasswd file path
1. Set your files, one per line, descriptive name without spaces and file.
1. Set your protected names, one per line, with the same names like files.
1. And run your server as pserver


There is a example .ini per backend:

1. dhcpd-development.ini
1. bind9-development.ini
