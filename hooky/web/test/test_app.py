from tornado import testing

from hooky import runserver
from hooky import utils
from hooky.web import app


class TestApp(testing.AsyncHTTPTestCase):
    def get_app(self):
        # Generate a real application server based on our test config data
        cfg = runserver.getConfigObject(
            'hooky.config.file.FileConfig',
            '%s/test_data/config.ini' % utils.getRootPath())
        server = app.getApplication(cfg)
        return server

    @testing.gen_test
    def testApp(self):
        """Test that the application starts up and serves basic requests"""
        self.http_client.fetch(self.get_url('/'), self.stop)
        response = self.wait()
        self.assertEquals(200, response.code)

    def testRootIncludesBasicTemplate(self):
        """Test that the index page includes/parses the template properly"""
        self.http_client.fetch(self.get_url('/'), self.stop)
        response = self.wait()
        self.assertIn('Welcome to Hooky', response.body)

    def testStaticContent(self):
        """Test that the /static/ content is served properly"""
        self.http_client.fetch(
            self.get_url('/static/bootstrap/css/bootstrap.css'), self.stop)
        response = self.wait()
        self.assertIn('Bootstrap v2', response.body)

    def testHookRoot(self):
        """Test that the /hook handler works properly"""
        self.http_client.fetch(self.get_url('/hook'), self.stop)
        response = self.wait()
        self.assertIn('githubToPost', response.body)

    def testHookServesSubmitTemplate(self):
        """Test that the /hook/githubToPost handler works properly"""
        self.http_client.fetch(self.get_url('/hook/githubToPost'), self.stop)
        response = self.wait()
        self.assertIn('githubToPost', response.body)
        self.assertIn('name="Submit"', response.body)
