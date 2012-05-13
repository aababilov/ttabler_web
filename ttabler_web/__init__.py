# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2011 Grid Dynamics Consulting Services, Inc.  All rights reserved.
#
#    This software is provided to Cisco Systems, Inc. as "Supplier Materials"
#    under the license terms governing Cisco's use of such Supplier Materials described
#    in the Master Services Agreement between Grid Dynamics Consulting Services, Inc. and Cisco Systems, Inc.,
#    as amended by Amendment #1.  If the parties are unable to agree upon the terms
#    of the Amendment #1 by July 31, 2011, this license shall automatically terminate and
#    all rights in the Supplier Materials shall revert to Grid Dynamics, unless Grid Dynamics specifically
#    and otherwise agrees in writing.

from flask import Flask

app = Flask("ttabler_web")

app.config.from_pyfile("/etc/ttabler-web/flask_settings.py")


from . import views 