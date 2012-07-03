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

    $ git://github.com/ant30/ninja-sysop.git

1. Create a virtualenv:

    $ virtualenv ninja-sysop

1. Load virtualenv:

    $ cd ninja-sysop
    $ source bin/activate

1. Deploy package as development:

    $ python setup.py development

1. To run the development server execute:

    $ pserve development.init --reload

1. Go to http://localhost:6543 to get Web Interface


The default login is defined on examples/htpasswd as admin/admin, you can
create many users as you need with htpasswd utility from apache2-tools



