import sys
if sys.version_info[:2] >= (2, 7):
    import unittest
else:
    try:
        import unittest2 as unittest
    except ImportError:
        raise ImportError("The unittest2 package is needed to run the tests.") 
del sys

from icarus.results import ResultSet

class TestResultSet(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.rs = ResultSet()
        cls.cond_a = {'alpha': 1, 'beta': 2, 'gamma': 3}
        cls.cond_b = {'alpha': 1, 'beta': 2, 'gamma': 3}
        cls.cond_c = {'alpha': -1, 'beta': -2, 'gamma': 3}
        cls.metric = {'m1': 1, 'm2': 2, 'm3': 3}
        cls.rs.add((cls.cond_a, cls.metric))
        cls.rs.add((cls.cond_b, cls.metric))
        cls.rs.add((cls.cond_c, cls.metric))
        pass
        
    @classmethod
    def tearDownClass(cls):
        pass
    
    def setUp(self):
        pass

    def tearDown(self):
        pass
    
    def test_len(self):
        self.assertEquals(3, len(self.rs))
    
    def test_getitem(self):
        cond, metric = self.rs[0]
        self.assertEquals(self.cond_a, cond)
        self.assertEquals(self.metric, metric)
        
    def test_filter_match(self):
        filtered_rs = self.rs.filter({'gamma': 3}, ['m1', 'm2'])
        self.assertEquals(3, len(filtered_rs))
        #TODO: Complete
        
    def test_filter_no_matching_metrics(self):
        filtered_rs = self.rs.filter({'gamma': 3}, ['mn'])
        self.assertEquals(3, len(filtered_rs))
        #TODO: Complete
        
    def test_filter_no_match(self):
        filtered_rs = self.rs.filter({'gamma': 3}, ['m1', 'm2'])
        self.assertEquals(3, len(filtered_rs))