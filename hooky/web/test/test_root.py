from tornado import web
from tornado import testing

from hooky.web import root
from hooky.version import __version__ as VERSION


class RootHandlerIntegrationTests(testing.AsyncHTTPTestCase):
    def get_app(self):
        return web.Application([('/', root.RootHandler)])

    @testing.gen_test
    def testIndexIncludesVersion(self):
        """Make sure the version number was presented properly"""
        self.http_client.fetch(self.get_url('/'), self.stop)
        response = self.wait()
        self.assertIn('Hooky v%s' % VERSION, response.body)
