# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Copyright 2013 Nextdoor.com

"""
"""

__author__ = 'matt@nextdoor.com (Matt Wise)'

import logging

from tornado import web

from hooky import utils
from hooky.web import hook
from hooky.web import root

log = logging.getLogger(__name__)


def getApplication(config):
    # Default list of URLs provided by Hooky and links to their classes
    URLS = [
        # Handle initial web clients at the root of our service.
        (r"/", root.RootHandler),

        # Provide access to our static content
        (r'/static/(.*)',
         web.StaticFileHandler,
         {'path': utils.getStaticPath()}),

        # Handle incoming hook requests
        (r"/hook", hook.HookRootHandler, {'config': config}),
        (r"/hook/(.*)", hook.HookHandler, {'config': config}),
    ]
    application = web.Application(URLS)
    return application
