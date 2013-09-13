import logging

from tornado.testing import unittest

from hooky import utils
from hooky import runserver
from hooky.config import file


class TestRunserver(unittest.TestCase):
    def testGetConfigObject(self):
        """Test the getConfigObject() method"""
        cfg_class = 'config.file.FileConfig'
        cfg_file = '%s/test_data/config.ini' % utils.getRootPath()

        cfg_object = runserver.getConfigObject(cfg_class, cfg_file)
        self.assertTrue(isinstance(cfg_object, file.FileConfig))

    def testGetRootLogger(self):
        """Test getRootLogger() method"""
        logger = runserver.getRootLogger('iNfO', 'level0')
        self.assertTrue(isinstance(logger, logging.RootLogger))
