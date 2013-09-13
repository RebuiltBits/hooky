# Copyright 2012 Nextdoor.com, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import sys
import shutil
import subprocess

from distutils.command.clean import clean
from distutils.command.sdist import sdist
from setuptools import Command
from setuptools import setup
from setuptools import find_packages

PACKAGE = 'hooky'
__version__ = None
execfile(os.path.join(PACKAGE, 'version.py'))  # set __version__


class CheckCommand(Command):
    descriptoin = 'Run tests.'
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        print 'Running pep8...'
        if subprocess.call(['pep8', 'hooky']):
            sys.exit('ERROR: failed pep8 checks')

        print 'Running pyflakes...'
        if subprocess.call(['pyflakes', 'hooky']):
            sys.exit('ERROR: failed pyflakes checks')

        print 'Running tests...'
        if subprocess.call(['coverage', 'run', '--source=hooky',
                            './setup.py', 'test']):
            sys.exit('ERROR: failed unit tests')
        subprocess.call(['coverage', 'report', '-m'])



class SourceDistHook(sdist):
    """Runs when creating the 'sdist' package.

    Makes sure to create a vesrion.rst file for the source package
    based on the version number found in the __version__ variable.
    """
    def run(self):
        with open('version.rst', 'w') as f:
            f.write(':Version: %s\n' % __version__)
        sdist.run(self)


class CleanHook(clean):
    def run(self):
        clean.run(self)

        def maybe_rm(path):
            if os.path.exists(path):
                try:
                    shutil.rmtree(path)
                except:
                    os.remove(path)

        maybe_rm('hooky.egg-info')
        maybe_rm('dist')
        maybe_rm('.coverage')
        maybe_rm('version.rst')
        maybe_rm('MANIFEST')


setup(
    name='hooky',
    version=__version__,
    description='Webhook Translation Gateway',
    long_description=open('README.md', 'r').read(),
    author='Matt Wise',
    author_email='matt@nextdoor.com',
    url='https://github.com/Nextdoor/hooky',
    download_url='http://pypi.python.org/pypi/hooky#downloads',
    license='Apache License, Version 2.0',
    keywords='web hook json post get',
    entry_points={
        'console_scripts': ['hooky = hooky.runserver:main'],
    },
    packages=find_packages(),
    test_suite='hooky',
    package_data={
        'hooky': [ 'test_data/*/*', 'test_data/config.ini',
                   'test_data/config_missing_general.ini',
                   'static/*.tmpl', 'static/templates/*.tmpl',
                   'static/templates/*/*.tmpl',
                   'static/bootstrap/*/*'],

    },
    setup_requires=[ 'setuptools', 'coverage', 'unittest2' ],
    install_requires=[
        'tornado',
        'pystache',
        'xmltodict',
        'setuptools',
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Topic :: Software Development',
        'License :: OSI Approved :: Apache Software License',
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Operating System :: POSIX',
        'Natural Language :: English',
    ],
    cmdclass={
        'sdist': SourceDistHook,
        'clean': CleanHook,
        'check': CheckCommand,
    },
)
