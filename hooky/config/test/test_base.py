from tornado.testing import unittest
import mock

from hooky.translators import base as TranslatorsBase
from hooky.config import base as ConfigBase


class TestBaseConfig(unittest.TestCase):
    def setUp(self):
        """Create our BaseConfig object for testing"""
        self.config = ConfigBase.BaseConfig()

    def testToBool(self):
        """Test the BaseConfig._toBool() method"""
        self.assertTrue(self.config._toBool('yes'))
        self.assertTrue(self.config._toBool('y'))
        self.assertTrue(self.config._toBool('true'))
        self.assertTrue(self.config._toBool('tRue'))
        self.assertTrue(self.config._toBool('t'))
        self.assertTrue(self.config._toBool('T'))
        self.assertTrue(self.config._toBool('1'))
        self.assertTrue(self.config._toBool(1))

        self.assertFalse(self.config._toBool(0))
        self.assertFalse(self.config._toBool('no'))
        self.assertFalse(self.config._toBool('No'))
        self.assertFalse(self.config._toBool('n'))
        self.assertFalse(self.config._toBool('f'))
        self.assertFalse(self.config._toBool('fAlse'))
        self.assertFalse(self.config._toBool('False'))
        self.assertFalse(self.config._toBool('no'))

        self.assertEquals(self.config._toBool('FooBar'), 'FooBar')

    def testAbstractness(self):
        """Tests that most methods are NotImplemented"""
        self.assertRaises(NotImplementedError, self.config.getGeneral)
        self.assertRaises(NotImplementedError, self.config.getHookList)
        self.assertRaises(NotImplementedError,
                          self.config.getHookConfig, 'bogus')
        self.assertRaises(NotImplementedError,
                          self.config._getTranslatorConfig, 'bogus')

    def testGetTranslator(self):
        """Tests the _getTranslator() method by mocking some objects"""
        # Build a TestTranslator configuration that our _getTranslatorConfig()
        # Mock method will return. This is used so that we are only testing
        # the _getTranslator() method here.
        test_cfg = {'translator': 'hooky.translators.base.TestTranslator',
                    'type': 'translator'}
        self.config._getTranslatorConfig = mock.Mock(return_value=test_cfg)
        returned_translator = self.config._getTranslator('unittest')

        # Make sure _getTranslator()  returns a TestTranslator object.
        self.assertTrue(isinstance(returned_translator,
                                   TranslatorsBase.TestTranslator))

    def testGetTranslatorBadConfig(self):
        """Tests that _getTranslator() raises proper exceptions"""
        # Build a TestTranslator configuration that our _getTranslatorConfig()
        # Mock method will return. This is used so that we are only testing
        # the _getTranslator() method here.
        test_cfg = {'translator': 'hooky.translators.base.BogusTranslator',
                    'type': 'translator'}
        self.config._getTranslatorConfig = mock.Mock(return_value=test_cfg)

        # Ensure that this raises a ConfigException because of
        # the bogus translator name.
        self.assertRaises(ConfigBase.ConfigException,
                          self.config._getTranslator,
                          'unittest')

    def testGetTranslators(self):
        """Tests that _getTranslators() executes properly"""
        # Build a TestTranslator object and mock the _getTranslator()
        # method to always return this mocked object.
        test_translator = TranslatorsBase.TestTranslator()
        self.config._getTranslator = mock.Mock(return_value=test_translator)

        # Build our exepcted list of translators
        expected_translators = [test_translator, test_translator]

        # Execute the _getTranslators() method with two translators listed
        # and validate the results against expected_translators.
        self.assertEquals(expected_translators,
                          self.config._getTranslators(['a', 'b']))
