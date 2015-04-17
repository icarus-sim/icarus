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

import icarus.scenarios as contentplacement


class TestUniform(unittest.TestCase):

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

    def test_uniform(self):
        t = fnss.line_topology(4)
        fnss.add_stack(t, 0, 'router')
        fnss.add_stack(t, 1, 'source')
        fnss.add_stack(t, 2, 'source')
        fnss.add_stack(t, 3, 'receiver')
        contentplacement.uniform_content_placement(t, range(10))
        c1 = t.node[1]['stack'][1]['contents']
        c2 = t.node[2]['stack'][1]['contents']
        self.assertEqual(len(c1) + len(c2), 10)
        
class TestWeighted(unittest.TestCase):

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

    def test_uniform(self):
        t = fnss.line_topology(4)
        fnss.add_stack(t, 0, 'router')
        fnss.add_stack(t, 1, 'source')
        fnss.add_stack(t, 2, 'source')
        fnss.add_stack(t, 3, 'receiver')
        contentplacement.weighted_content_placement(t, range(10), {1: 0.7, 2: 0.3})
        c1 = t.node[1]['stack'][1]['contents'] if 'contents' in t.node[1]['stack'][1] else set()
        c2 = t.node[2]['stack'][1]['contents'] if 'contents' in t.node[2]['stack'][1] else set()
        self.assertEqual(len(c1) + len(c2), 10)
        
    