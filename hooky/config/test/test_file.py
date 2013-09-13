from tornado.testing import unittest

from hooky import utils
from hooky.translators import base as TranslatorsBase
from hooky.translators import web
from hooky.config import base as ConfigBase
from hooky.config import file


class TestFileConfig(unittest.TestCase):
    def setUp(self):
        """Create our FileConfig object and test it """
        # Reference a few configuration files here so that throughout
        # our tests we can easily use them.
        self.configFile = '%s/test_data/config.ini' % utils.getRootPath()
        self.template_path = '%s/test_data/templates' % utils.getRootPath()

        # Create our FileConfig object for testing
        self.config = file.FileConfig(self.configFile)

    def testGetGeneral(self):
        """Test the getGeneral() method"""
        expected = {'templates': 'templates', 'unittest': True}
        self.assertEquals(expected, self.config.getGeneral())

    def testGetGeneralMissingSection(self):
        """Test that a missing [general] section is OK"""
        tmp_config = file.FileConfig('%s/test_data/config_missing_general.ini'
                                     % utils.getRootPath())
        self.assertEquals({}, tmp_config.getGeneral())

    def testMissingConfigFile(self):
        """Instantiating FileConfig with missing file should fail"""
        self.assertRaises(ConfigBase.ConfigException,
                          file.FileConfig,
                          'missing_config_file')

    def testGetTemplate(self):
        """Test the _getTemplate method"""
        # This is the file we'll submit, and compare against.
        template_file = '%s/GithubToHttpbinPost.tmpl' % self.template_path

        # Clear out any existing templates that have already been read in
        # and stored by other tests.
        self.config._template = {}

        # Verify that the returned data matches what we expect
        self.assertEquals(open(template_file, 'r').read(),
                          self.config._getTemplate(template_file))

        # Verify that the data was also stored in the local dict in the object
        self.assertEquals(open(template_file, 'r').read(),
                          self.config._templates[template_file])

        # Verify that a ConfigException is raised if the supplied file
        # is absent
        self.assertRaises(ConfigBase.ConfigException,
                          self.config._getTemplate,
                          'missing_file')

    def testGetHooks(self):
        """Test the getHookList() method"""
        expected = ['githubToPost', 'test']
        self.assertEquals(expected, self.config.getHookList())

    def testGetHook(self):
        """Test the getHookConfig() method"""
        # Requesting a section that is not of type 'hook'
        self.assertRaises(ConfigBase.ConfigException,
                          self.config.getHookConfig,
                          'general')

        # Test calling a hook that doesn't exist
        self.assertRaises(ConfigBase.ConfigException,
                          self.config.getHookConfig,
                          'missing_hook')

        # Normal tests that look for valid config data
        self.assertEquals(self.config.getHookConfig('githubToPost')['type'],
                          'hook')

    def testGetTranslatorList(self):
        """Test the _getTranslatorList() method"""
        expected = ['GithubToHttpbinPost',
                    'TestTranslator']

        self.assertEquals(expected, self.config._getTranslatorList())

    def testGetTranslatorConfig(self):
        """Test the _getTranslatorConfig() method"""
        template_file = '%s/GithubToHttpbinPost.tmpl' % self.template_path

        # Request the GithubToHttpbinPost translator thats fully configured
        returned = self.config._getTranslatorConfig('GithubToHttpbinPost')
        self.assertEquals(returned['content_type'], 'application/json')
        self.assertEquals(returned['translator'],
                          'hooky.translators.web.PostTranslator')
        self.assertEquals(returned['type'], 'translator')
        self.assertEquals(returned['url'], 'http://httpbin.org/post')
        self.assertEquals(returned['template'],
                          open(template_file, 'r').read())

        # Request the TestTranslator translator thats got no template
        returned = self.config._getTranslatorConfig('TestTranslator')
        self.assertEquals(returned['translator'],
                          'hooky.translators.base.TestTranslator')
        self.assertEquals(returned['type'], 'translator')

        # Test calling a translator that doesn't exist
        self.assertRaises(ConfigBase.ConfigException,
                          self.config._getTranslatorConfig,
                          'missing_translator')

        # Requesting a section that is not of type 'translator'
        self.assertRaises(ConfigBase.ConfigException,
                          self.config._getTranslatorConfig,
                          'general')

    def testGetTranslator(self):
        """Test actually retrieving a real Translator object"""
        template_file = '%s/GithubToHttpbinPost.tmpl' % self.template_path

        translator = self.config._getTranslator('GithubToHttpbinPost')
        self.assertEquals(translator.url, 'http://httpbin.org/post')
        self.assertEquals(translator.template,
                          open(template_file, 'r').read())

    def testGetTranslators(self):
        """Test the _getTranslators() method"""
        translators = self.config._getTranslators(['GithubToHttpbinPost',
                                                   'TestTranslator'])
        self.assertTrue(isinstance(translators[0], web.PostTranslator))
        self.assertTrue(isinstance(translators[1],
                                   TranslatorsBase.TestTranslator))
