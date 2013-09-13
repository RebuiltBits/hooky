from tornado import testing

from hooky import utils
from hooky.translators import web

# Defaults to use for the unit tests below
URL = 'http://httpbin.org/post'
CONTENT_TYPE = 'application/json'
TEMPLATE = '{\n "email": "{{pusher.email}}",\n "name": "{{pusher.name}}"\n}'
AUTH = 'user:pass'
AUTH_MODE = 'basic'


class PostTranslatorIntegrationTests(testing.AsyncTestCase):
    """These are integration tests for the PostTranslator object.

    These tests actually go out and call httpbin.org and perform real
    live calls to validate that things are working all the way through
    the code base.
    """
    def setUp(self):
        """Creates a PostTranslator object and mocks appropriate calls"""
        self.io_loop = self.get_new_ioloop()
        self.source_path = '%s/test_data/sources' % utils.getRootPath()

    @testing.gen_test
    def testSubmit(self):
        """Submits a GitHub webhook

        (https://help.github.com/articles/post-receive-hooks)"""
        # Get a valid Translator object
        translator = web.PostTranslator(URL, CONTENT_TYPE,
                                        TEMPLATE, AUTH, AUTH_MODE)

        # Get the data we're submitting from the large template
        test = open('%s/github.json' % self.source_path, 'r').read()

        # Expected results
        expected = {'success': True,
                    'message': 'OK'}

        # Call the submit method
        results = yield translator.submit(test)
        self.stop()

        # Are they the same?
        self.assertEquals(expected, results)

    @testing.gen_test
    def testBadSubmit(self):
        """Submits a GitHub webhook to an invalid URL.

        (https://help.github.com/articles/post-receive-hooks)"""
        # Get an INVALID Translator object
        translator = web.PostTranslator('http://httpbin.org/get',
                                        CONTENT_TYPE, TEMPLATE, AUTH,
                                        AUTH_MODE)

        # Get the data we're submitting from the large template
        # Get the data we're submitting from the large template
        test = open('%s/github.json' % self.source_path, 'r').read()

        # Expected results
        expected = {
            'success': False,
            'message': '2XX not returned: HTTP 405: Method Not Allowed'}

        # Call the submit method
        results = yield translator.submit(test)
        self.stop()

        # Are they the same?
        self.assertEquals(expected, results)

    @testing.gen_test
    def testSubmitWithBogusData(self):
        """Submits bogus data to the submit() method"""
        # Get an INVALID Translator object
        translator = web.PostTranslator('http://httpbin.org/get',
                                        CONTENT_TYPE, TEMPLATE, AUTH,
                                        AUTH_MODE)

        # Get the data we're submitting from the large template
        test = "<bogus_data>"

        # Expected results
        expected = {
            'success': False,
            'message': 'Supplied content is not valid '
                       'JSON or XML: <bogus_data>'}

        # Call the submit method
        results = yield translator.submit(test)
        self.stop()

        # Are they the same?
        self.assertEquals(expected, results)


class PostTranslatorUnitTests(testing.AsyncTestCase):
    """These are unit tests for the PostTranslator object.

    We mock the outbound HTTP calls and just test the code itself.
    """
    def setUp(self):
        """Creates a PostTranslator object and mocks appropriate calls"""
        self.translator = web.PostTranslator(URL, CONTENT_TYPE,
                                             TEMPLATE, AUTH, AUTH_MODE)
        self.io_loop = self.get_new_ioloop()
        self.source_path = '%s/test_data/sources' % utils.getRootPath()

    def testInit(self):
        """Make sure the object was initialized properly."""
        self.assertEquals(self.translator.url, URL)
        self.assertEquals(self.translator.template, TEMPLATE)
        self.assertEquals(self.translator.auth_mode, AUTH_MODE)
        self.assertEquals(self.translator.auth_username, 'user')
        self.assertEquals(self.translator.auth_password, 'pass')

    def testInitMissingAuth(self):
        """Make sure the object inits properly without any Auth info"""
        # Test with NO auth info sent
        translator = web.PostTranslator(URL, CONTENT_TYPE,
                                        TEMPLATE, None)
        self.assertEquals(translator.auth_username, None)
        self.assertEquals(translator.auth_password, None)

        # Test with BAD auth info sent
        try:
            web.PostTranslator(URL, CONTENT_TYPE,
                               TEMPLATE, 'bad_auth_info')
        except IndexError:
            threw_exception = True

        # Make sure the exception was indeed thrown
        self.assertTrue(threw_exception)
