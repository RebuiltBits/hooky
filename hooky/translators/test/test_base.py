import json

from tornado import testing
from tornado.testing import unittest
from tornado import httpclient

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
        req = httpclient.HTTPRequest('/', body=content)
        data = self.translator._request_to_dict(req)
        self.assertTrue(isinstance(data, dict))
        self.assertEquals(data['body']['ref'], 'refs/heads/master')
        self.assertEquals(data['body']['pusher']['email'], 'lolwut@noway.biz')

    def testXMLContentToDict(self):
        """Tests converting XML content to a dict"""
        content = open('%s/shopify.xml' % self.source_path, 'r').read()
        req = httpclient.HTTPRequest('/', body=content)
        data = self.translator._request_to_dict(req)
        self.assertTrue(isinstance(data, dict))
        self.assertEquals(data['body']['order']['billing-address']['address1'],
                          '123 Amoebobacterieae St')
        self.assertEquals(data['body']['order']['email'], 'bob@customer.com')


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
        d = {'foo': 'bar'}
        j = json.dumps(d)
        req = httpclient.HTTPRequest('/', body=j)

        # Call the submit method
        result = yield self.translator.submit(req)
        self.stop()

        # Are they the same?
        self.assertTrue(result['success'])
        self.assertIn('body.foo', result['message'])

    @testing.gen_test
    def testSubmitBogusData(self):
        """Test the submit() method with bogus data (should still work)"""
        # Simple data to submit
        req = httpclient.HTTPRequest('/', body="<bogus data>")

        # Call the submit method
        result = yield self.translator.submit(req)

        # Are they the same?
        self.assertEquals(result['success'], True)
