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
The FileConfig module uses ConfigParser as its backend for reading
and returning configuration results. The configuration is loaded up
once and is never re-read. Accesses to the public methods are very
fast and reliable because they rely entirely on the objects already
loaded into memory.

Detailed config file explanations can be found in config.ini.example.

Basic Configuration Fields:

    [general]
    templates: mytemplatedata

    [HookNameOne]
    type: hook
    translators: TranslatorOne, TranslatorTwo

    [TranslatorOne]
    type: translator
    translator: hooky.translators.web.PostTranslator
    url: http://mysite.com/post
    ...

    [TranslatorTwo]
    type: translator
    translator: hooky.translators.web.PostTranslator
    url: http://httpbin.org/post
    ...

Custom Translators:

If you build a custom translator, you can list it in the config just by
pointing to the package and class name on the translator line. Ie, if your
translator is in the 'custom_translators.py' file and the class name is
'MyTranslator' you would do something like this:

    [MyFunkyTranslator]
    type: translator
    translator: custom_translators.MyTranslator
    arg1: value1
    arg2: value2

Any arguments you list (other than 'type' and 'translator') will be passed
as keyword-arguments to your class at instantiation time.

Translator Templates:

If a template is found in 'templatedir/<translator section name>.tmpl' it will
be read in and sent as the 'template' kwarg to the translator class. If your
translator class requires a template (like the PostTranslator does), you
MUST have a matching template file as well.

In the example config above, you would need to have the following files:
    mytemplatedata/TranslatorOne.tmpl
    mytemplatedata/TranslatorTwo.tmpl

"""

__author__ = 'Matt Wise (wise@wiredgeek.net)'

import os
import logging

from ConfigParser import SafeConfigParser
from ConfigParser import NoSectionError

from hooky.config import base


log = logging.getLogger(__name__)


class FileConfig(base.BaseConfig):
    """A ConfigParser file-based implementation of the BaseConfig object.

    This object implements the BaseConfig methods, using the ConfigParser
    python package as the backend for reading the configuration data.
    """

    def __init__(self, config='config.ini'):
        """Read the initial configuration into ConfigParser objects"""
        log.info('Instantiating FileConfig with config file: %s' % config)

        # Create a single SafeConfigParser() object to use throughout the
        # lifetime of this object.
        self._parser = SafeConfigParser()

        # Create a blank dict to store already-read templates in from the
        # _getTemplate() method. This prevents re-reads of templates.
        self._templates = {}

        # ConfigParser does not return any failures if there is no config
        # file read in ... it just returns an empty list. If the list is
        # empty, bail.
        try:
            self._config = self._parser.read(config)[0]
        except IndexError:
            raise base.ConfigException('No configuration files found: %s' %
                                       config)

    def getGeneral(self):
        """Returns the global Hooky configuration parameters.

        returns:
            A dictionary object that looks something like:
                { 'templates': '/template_data' }
        """

        # Create a new blank config dict and append defaults.
        config = {}

        # Walk thouggh the 'general' section of the config file and add the
        # values that have been customized.
        try:
            for option in self._parser.options('general'):
                # Check if the option is meant to be a Bool or not.
                config[option] = self._toBool(self._parser.get('general',
                                                               option))
        except NoSectionError:
            # No specific general section, use the defaults.
            pass

        return config

    def getHookList(self):
        """Returns a list of the configured inbound webhook names.

        returns:
            [ 'HookA', 'HookB', ...]
        """
        hooks = []
        for section in self._parser.sections():
            if ('type' in self._parser.options(section) and
                    self._parser.get(section, 'type') == 'hook'):
                hooks.append(section)

        return hooks

    def getHookConfig(self, name):
        """Returns configuration parameters for the supplied hook name.

        Returns both the Hook configuration data as well as a list of
        fully configured Translator objects associated with that hook.

        args:
            name: String representing the name of the hook

        returns:
            A dictionary object that looks something like:
                { 'translators': [ <PostTranslator>] ,
                  'type': 'hook',
                  'url': 'http://httpbin.org',
                }

        raises:
            ConfigException if the supplied name does not exist
        """
        # If the requested config section doesn't exist, bail.
        if name not in self.getHookList():
            raise base.ConfigException('Hook "%s" does not exist in config' %
                                       name)

        # Create the new section in the config dict
        config = {}

        # Walk thouggh the hook name section of the config file and
        # add the values
        for option in self._parser.options(name):
            if option == 'translators':
                # Handle Translators specially. We actually will create full
                # Translator objects and pass references back in a list.
                translator_string = self._parser.get(name, option)
                translator_list = map(str.strip, translator_string.split(','))
                config[option] = self._getTranslators(translator_list)
            else:
                # Check if the option is meant to be a Bool or not.
                config[option] = self._toBool(self._parser.get(name, option))

        return config

    def _getTranslatorList(self):
        """Returns a list of the configured translator names.

        returns:
            [ 'TranslatorA', 'TranslatorB', ...' ]
        """
        translators = []
        for section in self._parser.sections():
            if ('type' in self._parser.options(section) and
                    self._parser.get(section, 'type') == 'translator'):
                translators.append(section)

        return translators

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
        if name not in self._getTranslatorList():
            raise base.ConfigException('Translator "%s" does not exist '
                                       'in config' % name)

        # Create a fresh config hash thats empty
        config = {}

        # Walk through the translator name sections of the config file
        # and add the values.
        for option in self._parser.options(name):
            config[option] = self._toBool(self._parser.get(name, option))

        # Look for a template that matches the name of the hook itself. If
        # one exists, read it in. If not, move on. If there is already a
        # configured 'template' option in the config file, then we skip
        # this.
        if 'template' not in config:
            # Build the absolute path to where the template SHOULD be. The
            # 'general' section should have a 'templates' option that defines
            # where the templates are. First, figure out if thats an absolute
            # or relative path.
            tmpl_path = self.getGeneral()['templates']
            if not os.path.isabs(tmpl_path):
                config_path = os.path.abspath(os.path.dirname(self._config))
                tmpl_path = '%s/%s' % (config_path, tmpl_path)

            tmpl_file_name = '%s/%s.tmpl' % (tmpl_path, name)

            log.debug('Looking for %s' % tmpl_file_name)

            try:
                config['template'] = self._getTemplate(tmpl_file_name)
            except base.ConfigException:
                # If no template exists, thats OK. Its possible that the
                # Translator doesn't need one. Just pass.
                pass

        return config

    def _getTemplate(self, filename):
        """Retrieves the Template from the supplied filename.

        Opening and closing file handles every time we are asked for a
        specific Hook config in getHookConfig() would be terribly inefficient,
        and also creates the possibility for strange behavior -- if the local
        template file changes as well as the config.ini file, the template
        changes would take effect immediately while the config.ini file is
        not re-read on every query.

        This method opens up a template if it has not yet been loaded, and then
        stores the data in a local dict for fast retrieval.

        args:
            filename: The absolute path to the filename of the template

        returns:
            String contents of the file

        re:
            ConfigException if the template does not exist
        """
        if not filename in self._templates:
            try:
                fh = open(filename, 'r')
            except IOError:
                # Its entirely OK that no template was found, depending on the
                # Hooky Translator thats used. Just log this out for debug.
                raise base.ConfigException('%s not found' % filename)
            else:
                self._templates[filename] = fh.read()
                fh.close()
                del fh

        return self._templates[filename]
