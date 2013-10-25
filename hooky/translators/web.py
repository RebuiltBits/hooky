import logging

from tornado import gen
from tornado import httpclient

import pystache

from hooky.translators import base

log = logging.getLogger(__name__)


class PostTranslator(base.BaseTranslator):
    """Translates a given webhook input into an outbound POST webhook.

    An instance of this class is configured with a translation description.
    This object will translate the hook, and then make the remote webhook call.

    Each Translator object is designed to only provide one type of translation,
    which keeps the code relatively simple and well enxapsulated. Additionally,
    since this object has to turn an arbitrary set of inputs into live Python
    objects, its recommended that you create a new Translator object for every
    single web hook submitted... this makes it less likely that we will end
    up with object references that prevent garbage collection.
    """

    def __init__(self, url, content_type, template, auth=None,
                 auth_mode='basic'):
        """Initiates the object and sanity checks the config.

        args:
            url: String represnting the remote webhook URL
            content_type: String representing the content encoding
            template: The template to use as the remote webhook data
        """

        # Test our config before creating the object
        log.debug('Initializing Translator object...')

        # The URL is valid... save it.
        self.auth_mode = auth_mode
        self.url = url
        self.template = template
        self.headers = {'Content-Type': content_type}

        # If the auth information was supplied, turn it into a Tuple and save
        # it appropriately.
        try:
            auth_array = auth.split(':')
            self.auth_username = auth_array[0]
            self.auth_password = auth_array[1]
        except IndexError:
            log.warning('Invalid auth data supplied: %s' % auth)
            raise
        except AttributeError:
            self.auth_username = None
            self.auth_password = None

    @gen.coroutine
    def submit(self, request):
        """Translates an incoming webchook and submits it to the dest service

        args:
            request: Tornado HTTPRequest Object
        """
        # Parse the incoming data into a dict that we can handle
        data = self._request_to_dict(request)

        # Parse our incoming data against our template and generate the
        # outbound POST body string.
        post_body = pystache.render(self.template, data)

        # Build our Async HTTP client object as well as the request object
        http_client = httpclient.AsyncHTTPClient()
        http_request = httpclient.HTTPRequest(
            url=self.url,
            method='POST',
            body=post_body.encode('UTF-8'),
            headers=self.headers,
            auth_username=self.auth_username,
            auth_password=self.auth_password,
            auth_mode=self.auth_mode,
            follow_redirects=True,
            max_redirects=10,
            user_agent='Hooky')

        # Throw the request into the IOLoop for execution..
        try:
            http_response = yield http_client.fetch(http_request)
            response = {'success': True,
                        'message': http_response.reason}
        except Exception, e:
            response = {'success': False,
                        'message': '2XX not returned: %s' % e}

        log.debug('Response: %s' % response)
        raise gen.Return(response)
