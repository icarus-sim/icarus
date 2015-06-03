import sys
if sys.version_info[:2] >= (2, 7):
    import unittest
else:
    try:
        import unittest2 as unittest
    except ImportError:
        raise ImportError("The unittest2 package is needed to run the tests.") 
del sys

import icarus.scenarios as topology


class TestTree(unittest.TestCase):

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

    def test_tree(self):
        t = topology.topology_tree(2, 3)
        self.assertEqual(6, len(t.graph['icr_candidates']))
        self.assertEqual(1, len(t.sources()))
        self.assertEqual(8, len(t.receivers()))
        

class TestPath(unittest.TestCase):

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

    def test_path(self):
        t = topology.topology_path(5)
        self.assertEqual(3, len(t.graph['icr_candidates']))
        self.assertEqual(1, len(t.sources()))
        self.assertEqual(1, len(t.receivers()))
        

class TestRocketFuel(unittest.TestCase):

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

    def test_rocketfuel(self):
        t = topology.topology_rocketfuel_latency(1221, 0.1, 20)
        self.assertEqual(len(t.receivers()), len(t.graph['icr_candidates']))
