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
# Copyright 2013 Nextdoor.com, Inc

import json
import logging

from tornado import gen

from xml.parsers.expat import ExpatError
import pystache
import xmltodict

log = logging.getLogger(__name__)


class ContentException(Exception):
    """Raised when the supplied webhook content is invalid"""


class RemoteHookException(Exception):
    """Raised when a remote hook failed to return a valid code"""


class BaseTranslator(object):
    """Abstract class that describes a Translator class in Hooky.

    An Translator instance is configured with enough information to translate
    an incoming webhook into whatever the outbound format is, and executes
    that translation every time the submit() method is called.

    A single call to the submit() method yields a generator that allows the
    Tornado IOLoop to continue operating on other requests.
    """

    def submit(self, content):
        """Generator that translates content into an outbound hook.

        This method takes in the content (request body, or arguments),
        translates them into an appropriate outbound template and operates
        in an asynchronous way on that template.

        Rather than returning a result, this method must be wrapped by
        @tornado.gen.coroutine, and when finished handling its data
        (with all exceptions caught and handled internally), it must
        raise tornado.gen.Return(<response value>) to pass the data back
        to the caller.

        args:
            content: String value of the content supplied by the web call.
        """
        raise NotImplementedError('Not implemented. Use one of my subclasses.')

    def _content_to_dict(self, content):
        """Translates supplied content into a dictionary.

        Walks through the supplied content (arguments, or request body) and
        tries to translate it into a dictionary. Supports inbound XML, JSON
        and request argument dictionaries.

        args:
            content: String value of the content to convert to a dict

        returns:
            data: A dictionary of data

        raises:
            ContentException: If the content cannot be converted into a dict
        """
        # If content is already a dict, just return it
        if isinstance(content, dict):
            log.debug('Content is dict...')
            return content

        # See if the data is JSON
        try:
            log.debug('Attempting to parse supplied content as JSON')
            data = json.loads(content)
        except (ValueError, TypeError):
            log.debug('Content is not JSON...')
            pass
        else:
            log.debug('Content is JSON...')
            return data

        # See if the data is XML
        try:
            log.debug('Attempting to parse supplied content as XML')
            data = xmltodict.parse(content)
        except ExpatError:
            log.debug('Content is not XML...')
            pass
        else:
            log.debug('Content is XML...')
            return data

        # If we got here, we've run out of possibilities. Raise an exception.
        raise ContentException('Supplied content is not valid JSON or XML: %s'
                               % content)


class TestTranslator(BaseTranslator):
    """Returns a string of potential Webhook variables.

    This translator will parse the incoming webhook data, and then generate
    and return a document describing all available variables that can be
    used in a new outbound webhook template. This is primarily used for helping
    a user create new webhook translations.
    """

    def __init__(self):
        """Initiates the object and sanity checks the config. """
        log.debug('Initializing TestTranslator object...')

    @gen.coroutine
    def submit(self, content):
        """Translates an incoming webchook and returns a predefined template.

        args:
            content: A string containing the incoming webhook data.

        raises:
            doc: A listing of all possible fields that were submitted
                 with the incoming webhook.
        """
        log.debug('%s beginning...' % self)

        # Parse the incoming data into a dict that we can handle
        try:
            data = self._content_to_dict(content)
        except ContentException, e:
            log.debug('Error')
            response = ({'success': False, 'message': format(str(e))})
            raise gen.Return(response)

        # Now that we have the dict, create a dynamic template that lists
        # all of the keys in that dict.
        template = self._createTemplate(data)

        # Generate our parsed template now
        content = pystache.render(template, data)

        # return the template
        response = ({'success': True, 'message': content})
        raise gen.Return(response)

    def _createTemplate(self, data):
        """Creates a dynamic template with all of the Keys

        args:
            data: Dictionary of Key/Value pairs

        returns:
            doc: A string with all of the key/value pairs listed
                 in Pystache format.
        """

        # Quick local method used to turn our dict into keys recursively.
        def flatten_dict_to_keys_only(init, lkey=''):
            ret = []
            for rkey, val in init.items():
                key = lkey+rkey
                if isinstance(val, dict):
                    ret = ret + flatten_dict_to_keys_only(val, key+'.')
                else:
                    ret.append(key)
            return ret

        # Get our key list now and sort it alphabetically
        keys = flatten_dict_to_keys_only(data)
        keys.sort()

        # Prep our string header and set the default delimiter
        # in pystache to < and > rather than {{ }}. This will allow
        # us to actually use {{ and }} below to show the user how
        # the formatting should look.
        string = "Key Name => Key value\n{{=< >=}}"

        # Now, for each key we save a line to our string
        for key in keys:
            line = '{{%s}} => < %s >' % (key, key)
            string = "%s\n%s" % (string, line)

        return string
