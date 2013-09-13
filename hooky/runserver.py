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
Hooky main server initialization script.

This is the main initialization code for the Hooky daemon. Command-line
options are documented more thoroughly in the README file.
"""

__author__ = 'Matt Wise (matt@nextdoor.com)'

from tornado import ioloop
import optparse

from hooky import utils
from hooky.web import app

from version import __version__ as VERSION

# Default parameters
DEFAULT_CONFIG_PROVIDER = 'hooky.config.file.FileConfig'
DEFAULT_CONFIG_FILE = 'config.ini'

# Initial option handler to set up the basic application environment.
usage = 'usage: %prog <options>'
parser = optparse.OptionParser(usage=usage, version=VERSION,
                               add_help_option=True)
parser.set_defaults(verbose=True)
parser.add_option('-C', '--configModule', dest='config_module',
                  default=DEFAULT_CONFIG_PROVIDER,
                  help='Override the default configuration provider (def: %s)'
                        % DEFAULT_CONFIG_PROVIDER),
parser.add_option('-c', '--configFile', dest='config_file',
                  default=DEFAULT_CONFIG_FILE,
                  help='Override the default file (def: %s)'
                        % DEFAULT_CONFIG_FILE),
parser.add_option('-p', '--port', dest='port',
                  default='8080',
                  help='Port to listen to (def: 8080)',)
parser.add_option('-l', '--level', dest="level",
                  default='warn',
                  help='Set logging level (INFO|WARN|DEBUG|ERROR)')
parser.add_option('-s', '--syslog', dest='syslog',
                  default=None,
                  help='Log to syslog. Supply facility name. (ie "local0")')
(options, args) = parser.parse_args()


def getConfigObject(config_module, config_file):
    """Constructs and returns a Config object"""
    config_class = utils.strToClass(config_module)
    config_object = config_class(config_file)
    return config_object


def getRootLogger(level, syslog):
    """Configures our Python stdlib Root Logger"""
    # Convert the supplied log level string
    # into a valid log level constant
    level_string = 'logging.%s' % level.upper()
    level_constant = utils.strToClass(level_string)

    # Set up the logger now
    return utils.setupLogger(level=level_constant, syslog=syslog)


def main():
    # Set up logging
    log = getRootLogger(options.level, options.syslog)

    # Create our configuration object
    log.debug('Building config object...')
    cfg = getConfigObject(options.config_module, options.config_file)

    # Build the HTTP service listening to the port supplied
    server = app.getApplication(cfg)
    server.listen(int(options.port))
    ioloop.IOLoop.instance().start()


if __name__ == '__main__':
    main()
