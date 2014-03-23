import sys
if sys.version_info[:2] >= (2, 7):
    import unittest
else:
    try:
        import unittest2 as unittest
    except ImportError:
        raise ImportError("The unittest2 package is needed to run the tests.") 
del sys
import fnss

import icarus.util as util


class TestUtil(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass    
    
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_timestr(self):
        self.assertEqual("1m 30s", util.timestr(90, True))
        self.assertEqual("1m", util.timestr(90, False))
        self.assertEqual("2m", util.timestr(120, True))
        self.assertEqual("21s", util.timestr(21, True))
        self.assertEqual("0m", util.timestr(21, False))
        self.assertEqual("1h", util.timestr(3600, True))
        self.assertEqual("1h", util.timestr(3600, False))
        self.assertEqual("1h 0m 4s", util.timestr(3604, True))
        self.assertEqual("1h", util.timestr(3604, False))
        self.assertEqual("1h 2m 4s", util.timestr(3724, True))
        self.assertEqual("1h 2m", util.timestr(3724, False))
        self.assertEqual("2d 1h 3m 9s", util.timestr(49*3600 + 189, True))
        self.assertEqual("0s", util.timestr(0, True))
        self.assertEqual("0m", util.timestr(0, False))