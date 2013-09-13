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
# Copyright 2013 Nextdoor.com, Inc.

"""
This package handles the actual webhook part of the service. Incoming
web requests are routed here, parsed, and passed off to Hook resources
for processing.

The HookRouter is the router interface that accepts any web call to
/hook/XXX and handles creating the appropriate Hook resource for the
supplied hook name (XXX).

Individual Hook resources are created for each and every web request --
which increases the CPU workload a bit in high frequency applications,
but reduces code complexity and object cleanup significantly.
"""

__author__ = 'matt@nextdoor.com (Matt Wise)'

import logging

from tornado import gen
from tornado import template
from tornado import web

from hooky import utils

log = logging.getLogger(__name__)


class HookConfigException(Exception):
    """Raised when an individual Hook is configured improperly."""


class HookRootHandler(web.RequestHandler):
    """Serves up the /hook index page"""

    def initialize(self, config):
        """Stores the supplied config object for later use

        args:
            config: A hooky.config.base.BaseConfig conforming object
        """
        log.debug('%s initialized %s with %s' % (self.__class__, self, config))
        self.config = config
        self.loader = template.Loader('%s/templates' %
                                      utils.getStaticPath())

    def get(self):
        """Render the hook list web page"""
        hooks = self.config.getHookList()
        self.write(self.loader.load('hook/index.tmpl').generate(hooks=hooks))


class HookHandler(web.RequestHandler):
    """Handles distributing the web request to the right translators.

    The Hook RequestHandler is actually responsible for accepting the inbound
    web hook content (JSON, XML, POST/PUT, etc), and passing it along to the
    configured Translator objects.

    A single HookHandler is created to handle each inbound web request. The
    appropriate Translator object is instantiated and called, and the client
    waits until the Translator object is done doing its work before being given
    a proper response code.

    Response Codes:
      200: All translations happened sucessfully
      502: At least one translation failed 'upstream'
      503: An internal application error occurred during translation

    """
    def initialize(self, config):
        """Stores the supplied config object for later use

        args:
            config: A hooky.config.base.BaseConfig conforming object
        """
        log.debug('%s initialized %s with %s' % (self.__class__, self, config))
        self.config = config
        self.loader = template.Loader('%s/templates' %
                                      utils.getStaticPath())

    @gen.coroutine
    def submitToTranslators(self, data, translators):
        """Submits the work to the translators and handles the response.

        This method calls out to the translator[0] object submit() method
        and waits (asyncronously) for a response. When the response comes,
        it parses it for success/failure and returns the appropriate data
        to the end-user.

        args:
            response: A dictionary that contains a 'success' and 'message'
                      key that describe the results. The 'success' key must
                      be a Boolean. eg:

                      {'success': True, 'message': 'OK' }
        """
        response = yield translators[0].submit(data)

        log.debug('Translator response: %s' % response)
        try:
            success = response['success']
            message = response['message']
        except AttributeError, e:
            log.error('Translator returned invalid results: %s' % e)
            self.send_error(503)

        if not success:
            log.error('Translator returned failure: %s' % success)
            self.set_status(502)
        else:
            self.set_status(200)

        self.write("Results: %s " % message)
        self.finish()

    @gen.coroutine
    def handleInitialRequest(self, data, hook):
        # As long as a hook name is supplied, get the list of translators
        translators = self.config.getHookConfig(hook)['translators']

        # Determine whether or not individual arguments were passed via the
        # GET call. If no arguments were passed, render a generic page where
        # data can be manually submitted.
        #if ((hook is not None or '/') and (self.request.arguments is {})):
        if (data == {} or data is None or data == ''):
            data = {'name': hook, 'translators': translators}
            self.write(self.loader.load('hook/submit.tmpl').generate(**data))
            return

        # Post body data takes precedence over arguments passed on the
        # hook URI line.
        log.debug('Passing supplied data to translators: %s' % translators)
        yield self.submitToTranslators(data, translators)

    @gen.coroutine
    def get(self, hook):
        """Renders a page describing the inbound hook and how to use it."""
        # Pass the args into our translator
        yield self.handleInitialRequest(self.request.arguments, hook)

    @gen.coroutine
    def post(self, hook):
        # Pass the args into our translator
        yield self.handleInitialRequest(self.request.body, hook)

    @gen.coroutine
    def put(self, hook):
        # Pass the args into our translator
        yield self.handleInitialRequest(self.request.body, hook)
