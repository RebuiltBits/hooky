from tornado import web
from tornado import testing
from tornado import httpclient

from hooky import utils
from hooky import runserver
from hooky.web import hook


class HookHandlerIntegrationTests(testing.AsyncHTTPTestCase):
    def get_app(self):
        cfg_class = 'config.file.FileConfig'
        cfg_file = '%s/test_data/config.ini' % utils.getRootPath()
        config = runserver.getConfigObject(cfg_class, cfg_file)

        URLS = [
            ('/hook', hook.HookRootHandler, {'config': config}),
            (r"/hook/(.*)", hook.HookHandler, {'config': config})]

        return web.Application(URLS)

    @testing.gen_test
    def testIndexLinksHooks(self):
        """Make sure the hooks are linked"""
        self.http_client.fetch(self.get_url('/hook'), self.stop)
        response = self.wait()
        self.assertIn('<a href=\'/hook/githubToPost\'>githubToPost</a>',
                      response.body)
        self.assertIn('<a href=\'/hook/test\'>test</a>', response.body)
        self.assertEquals(200, response.code)

    @testing.gen_test
    def testHookGet(self):
        """Test 'test' hook with GET method"""
        # Test 1: With an argument
        self.http_client.fetch(self.get_url('/hook/test?foo=bar&foo=baz'),
                               self.stop)
        response = self.wait()
        self.assertIn('{{foo}} => [\'bar\', \'baz\']', response.body)
        self.assertEquals(200, response.code)

        # Test 2: No arguments
        self.http_client.fetch(self.get_url('/hook/test'), self.stop)
        response = self.wait()
        self.assertIn('Raw Post Data', response.body)
        self.assertEquals(200, response.code)

    @testing.gen_test
    def testHookPOST(self):
        """Test 'test' hook with POST method"""
        # Test 1: With an argument
        req = httpclient.HTTPRequest(
            url=self.get_url('/hook/test'),
            method='POST',
            body='{"foo":"bar"}')
        self.http_client.fetch(req, self.stop)
        response = self.wait()
        self.assertIn('{{foo}} => bar', response.body)
        self.assertEquals(200, response.code)

        # Test 2: Empty POST Body
        req = httpclient.HTTPRequest(
            url=self.get_url('/hook/test'),
            method='POST',
            body='')
        self.http_client.fetch(req, self.stop)
        response = self.wait()
        self.assertIn('Raw Post Data', response.body)
        self.assertEquals(200, response.code)

        # Test 3: With an argument
        req = httpclient.HTTPRequest(
            url=self.get_url('/hook/test'),
            method='POST',
            body='<xml> oo":"bar"}')
        self.http_client.fetch(req, self.stop)
        response = self.wait()
        self.assertIn('is not valid', response.body)
        self.assertEquals(502, response.code)

    @testing.gen_test
    def testHookPUT(self):
        """Test 'test' hook with PUT method"""
        # Test 1: With an argument
        req = httpclient.HTTPRequest(
            url=self.get_url('/hook/test'),
            method='PUT',
            body='{"foo":"bar"}')
        self.http_client.fetch(req, self.stop)
        response = self.wait()
        self.assertIn('{{foo}} => bar', response.body)
        self.assertEquals(200, response.code)

        # Test 2: Empty PUT Body
        req = httpclient.HTTPRequest(
            url=self.get_url('/hook/test'),
            method='PUT',
            body='')
        self.http_client.fetch(req, self.stop)
        response = self.wait()
        self.assertIn('Raw Post Data', response.body)
        self.assertEquals(200, response.code)

        # Test 3: With an argument
        req = httpclient.HTTPRequest(
            url=self.get_url('/hook/test'),
            method='POST',
            body='<xml> oo":"bar"}')
        self.http_client.fetch(req, self.stop)
        response = self.wait()
        self.assertIn('is not valid', response.body)
        self.assertEquals(502, response.code)
