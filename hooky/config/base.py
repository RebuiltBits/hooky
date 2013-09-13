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

"""
Configuration Objects for Hooky.

This package provides different Config object models for the Hooky service.
Each object must conform to the basic standard below, but can implement
that standard any way you choose.
"""

__author__ = 'Matt Wise (wise@wiredgeek.net)'

import logging

from hooky import utils


log = logging.getLogger(__name__)


class ConfigException(Exception):
    """Raised when the Configuration data is invalid for some reason"""


class BaseConfig(object):
    """Abstract object that defines the public methods for a Config object"""
    abstract = True

    def getGeneral(self):
        """Returns the global Hooky configuration parameters.

        returns:
            A dictionary object that looks something like:
                { 'templates': '/template_data', }
        """
        raise NotImplementedError('Not implemented. Use one of my subclasses.')

    def getHookList(self):
        """Returns a list of our configured hook names.

        returns:
            [ 'HookA', 'HookB', etc...]
        """
        raise NotImplementedError('Not implemented. Use one of my subclasses.')

    def getHookConfig(self, name):
        """Returns configuration parameters for the supplied hook name.

        Returns both the Hook configuration data as well as fully configured
        Translator objects associated with that hook.

        args:
            name: String representing the name of the hook

        returns:
            A dictionary object that looks something like:
                { 'translators': [ <GithubTranslator>, <FooBarTranslator> ] }
        """
        raise NotImplementedError('Not implemented. Use one of my subclasses.')

    def _getTranslatorConfig(self, name):
        """Returns a Translator configuration.

        args:
            name: String representing the name of the translator

        returns:
            A dictionary object that looks something like:
                { 'translator': 'PostTranslator',
                  'url': 'http://foobar.com',
                  'content_type': 'application/json',
                  'template': '<some template here>',
                }
        """
        raise NotImplementedError('Not implemented. Use one of my subclasses.')

    def _getTranslator(self, name):
        """Returns a Translator object.

        Returns a fully built Translator object based on the config supplied.
        As long as a subclassed Config object does not add any additional
        custom fields, this method can be used as-is.

        args:
            name: String representing the name of the translator

        returns:
            A Translator object built with the config parameters returned by
            self._getTranslatorConfig().
        """
        # Get the configuration for a supplied Translator definition.
        config = self._getTranslatorConfig(name)
        class_string = config['translator']

        # There are a few parameters that are stored for each Translator
        # definition that we do not pass in as arguments to the __init__()
        # method:
        #
        # type: This is an internal config value used to distinguish between
        #       Hook and Translator configs.
        #
        # translator: This is an internal config value that defines the class
        #             and package name used to instantiate a new Translator.
        del config['type']
        del config['translator']

        # Now instantiate the class and return it.
        try:
            return utils.strToClass(class_string)(**config)
        except AttributeError:
            raise ConfigException('Unable to convert "%s" to a proper object'
                                  % class_string)

    def _getTranslators(self, translators):
        """Returns a list of fully instantiated Translator objects.

        Takes in an list of Translator definitions and turns them into real
        configured Translator objects.

        args:
            translator: A list of translator definition string names

        returns:
            A list of fully built Translator objects
        """
        log.debug('Building Translators: %s' % translators)

        # Create a new array to store these Translators in
        objects = []

        # For each one, go and create it and append it to the list
        for definition in translators:
            translator = self._getTranslator(definition)
            objects.append(translator)
            log.debug('Built %s' % translator)

        # Return the list now
        return objects

    def _toBool(self, value):
        """ Converts 'something' to boolean.

        Possible True  values: 1, True, "1", "TRue", "yes", "y", "t"
        Possible False values: 0, False, None, [], {}, "", "0",
                               "faLse", "no", "n", "f", 0.0, ...

        Returns original unmodified string if no match to above.
        """
        if str(value).lower() in ("yes", "y", "true",  "t", "1"):
            return True
        if str(value).lower() in ("no",  "n", "false", "f", "0", "0.0",
                                  "", "none", "[]", "{}"):
            return False
        return value
