from tornado import testing
from tornado.testing import unittest

from hooky import utils
from hooky.translators import base


class TestBaseTranslator(unittest.TestCase):
    def setUp(self):
        """Creates a PostTranslator object"""
        self.translator = base.BaseTranslator()
        self.source_path = '%s/test_data/sources' % utils.getRootPath()

    def testSubmit(self):
        """Make sure submit() returns NotImplemented"""
        self.assertRaises(NotImplementedError,
                          self.translator.submit,
                          'foo')

    def testJSONContentToDict(self):
        """Tests converting JSON content to a dict"""
        content = open('%s/github.json' % self.source_path, 'r').read()
        data = self.translator._content_to_dict(content)
        self.assertTrue(isinstance(data, dict))
        self.assertEquals(data['ref'], 'refs/heads/master')
        self.assertEquals(data['pusher']['email'], 'lolwut@noway.biz')

    def testXMLContentToDict(self):
        """Tests converting XML content to a dict"""
        content = open('%s/shopify.xml' % self.source_path, 'r').read()
        data = self.translator._content_to_dict(content)
        self.assertTrue(isinstance(data, dict))
        self.assertEquals(data['order']['billing-address']['address1'],
                          '123 Amoebobacterieae St')
        self.assertEquals(data['order']['email'], 'bob@customer.com')

    def testDictContentToDict(self):
        """Tests converting dict content to a dict"""
        content = {'foo': 'bar', 'baz': 'boo'}
        data = self.translator._content_to_dict(content)
        self.assertTrue(isinstance(data, dict))
        self.assertEquals(data, content)

    def testBogusContentToDict(self):
        """Bad content raises a ContentException"""
        self.assertRaises(base.ContentException,
                          self.translator._content_to_dict,
                          'bogus_data')


class TestTestTranslator(testing.AsyncTestCase):
    def setUp(self):
        """Creates a TestTranslator object"""
        self.translator = base.TestTranslator()
        self.io_loop = self.get_new_ioloop()

    def testCreateTemplate(self):
        """Test the _createTemplate() method"""
        test = {'foo': 'bar',
                'foobar': {'xyz': '123'}}
        returned = self.translator._createTemplate(test)
        self.assertIn('{{foo}}', returned)
        self.assertIn('{{foobar.xyz}}', returned)

    def testCreateTemplateEmptyDict(self):
        """Test the _createTemplate() method with an empty dict"""
        test = {}
        returned = self.translator._createTemplate(test)
        self.assertIn('{{=< >=}}', returned)

    @testing.gen_test
    def testSubmit(self):
        """Test the submit() method"""
        # Simple data to submit
        test = {'foo': 'bar'}

        # Expected results
        expected = {'success': True,
                    'message': 'Key Name => Key value\n{{foo}} => bar'}

        # Call the submit method
        result = yield self.translator.submit(test)
        self.stop()

        # Are they the same?
        self.assertEquals(result, expected)

    @testing.gen_test
    def testSubmitBogusData(self):
        """Test the submit() method with bogus data"""
        # Simple data to submit
        test = "<bogus data>"

        # Call the submit method
        result = yield self.translator.submit(test)

        # Are they the same?
        self.assertEquals(result['success'], False)
        self.assertIn('is not valid', result['message'])
