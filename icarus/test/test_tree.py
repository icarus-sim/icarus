import unittest

from io import BytesIO
try:
    # Python 2
    import cPickle as pickle
except ImportError:
    # Python 3
    import pickle

from icarus.util import Tree

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

    def test_init_from_tree(self):
        t = Tree({'a': 1, 'b': 2})
        tree = Tree(t)
        self.assertEqual(tree.getval(['a']), 1)
        self.assertEqual(tree.getval(['b']), 2)
        self.assertIsInstance(tree, Tree)

    def test_init_from_dict(self):
        tree = Tree({'a': 1, 'b': 2})
        self.assertEqual(tree.getval(['a']), 1)
        self.assertEqual(tree.getval(['b']), 2)
        self.assertIsInstance(tree, Tree)

    def test_init_from_kwargs(self):
        tree = Tree(a=1, b=2)
        self.assertEqual(tree.getval(['a']), 1)
        self.assertEqual(tree.getval(['b']), 2)
        self.assertIsInstance(tree, Tree)

    def test_init_from_nested_kwargs(self):
        tree = Tree(a=1, b=dict(c=2))
        self.assertEqual(tree.getval(['a']), 1)
        self.assertEqual(tree.getval(['b', 'c']), 2)
        self.assertIsInstance(tree, Tree)
        self.assertIsInstance(tree['b'], Tree)

    def test_init_from_dict_kwargs(self):
        tree = Tree({'c': 3}, a=1, b=2)
        self.assertEqual(tree.getval(['a']), 1)
        self.assertEqual(tree.getval(['b']), 2)
        self.assertEqual(tree.getval(['c']), 3)
        self.assertIsInstance(tree, Tree)

    def test_init_from_nested_dict(self):
        tree = Tree({'a': {'c': {'e': 1}}, 'b': {'d': 2}})
        self.assertEqual(tree.getval(['a', 'c', 'e']), 1)
        self.assertEqual(tree.getval(['b', 'd']), 2)
        self.assertIsInstance(tree, Tree)
        self.assertIsInstance(tree['a'], Tree)
        self.assertIsInstance(tree['a']['c'], Tree)
        self.assertIsInstance(tree.getval(['a', 'c']), Tree)
        self.assertIsInstance(tree['b'], Tree)

    def test_setitem(self):
        tree = Tree()
        tree['a'] = {'b': 1, 'c': 2}
        self.assertIsInstance(tree, Tree)
        self.assertIsInstance(tree['a'], Tree)
        self.assertEqual(tree.getval(['a', 'b']), 1)
        self.assertEqual(tree.getval(['a', 'c']), 2)

    def test_nested_setitem(self):
        tree = Tree()
        tree['a'] = {'b': {'c': 1}, 'd': 2}
        self.assertIsInstance(tree, Tree)
        self.assertIsInstance(tree['a'], Tree)
        self.assertIsInstance(tree['a']['b'], Tree)
        self.assertEqual(tree.getval(['a', 'b', 'c']), 1)
        self.assertEqual(tree.getval(['a', 'd']), 2)

    def test_update_base(self):
        tree = Tree()
        tree.update({'b': 1, 'c': 2})
        self.assertIsInstance(tree, Tree)
        self.assertEqual(tree.getval(['b']), 1)
        self.assertEqual(tree.getval(['c']), 2)

    def test_update_new_brach(self):
        tree = Tree()
        tree['a'].update({'b': 1, 'c': 2})
        self.assertIsInstance(tree, Tree)
        self.assertIsInstance(tree['a'], Tree)
        self.assertEqual(tree.getval(['a', 'b']), 1)
        self.assertEqual(tree.getval(['a', 'c']), 2)

    def test_nested_update(self):
        tree = Tree()
        tree['a'].update({'b': {'c': 1}, 'd': 2})
        self.assertIsInstance(tree, Tree)
        self.assertIsInstance(tree['a'], Tree)
        self.assertIsInstance(tree['a']['b'], Tree)
        self.assertEqual(tree.getval(['a', 'b', 'c']), 1)
        self.assertEqual(tree.getval(['a', 'd']), 2)

    def test_getset(self):
        tree = Tree()
        tree.setval([1, 2, 3, 4], 5)
        self.assertEqual(tree.getval([1, 2, 3, 4]), 5)

    def test_getval(self):
        tree = Tree()
        tree[1][2][3] = 4
        self.assertEqual(tree.getval([1, 2, 3]), 4)
        self.assertEqual(tree.getval([1, 2])[3], 4)
        self.assertEqual(tree.getval([1])[2][3], 4)

    def test_getval_none(self):
        tree = Tree()
        self.assertIsNone(tree.getval([1]))
        self.assertIsNone(tree.getval([1, 2]))
        self.assertIsNone(tree.getval([3, 4, 5]))

    def test_getval_empty(self):
        tree = Tree()
        _ = tree[1][2][3]
        self.assertIsNotNone(tree.getval([1]))
        self.assertIsNotNone(tree.getval([1, 2]))
        self.assertIsNone(tree.getval([1, 2, 3]))
        self.assertIsNone(tree.getval([1, 2, 3, 4]))

    def test_iter(self):
        tree = Tree()
        # add first elements
        tree['b']['c']['e'] = 4
        tree['b']['v']['d'] = 3
        l = list(tree)
        self.assertEquals(len(l), 2)
        self.assertIn((('b', 'c', 'e'), 4), l)
        self.assertIn((('b', 'v', 'd'), 3), l)
        # add additional element
        tree['a'] = 1
        l = list(tree)
        self.assertEquals(len(l), 3)
        self.assertIn((('b', 'c', 'e'), 4), l)
        self.assertIn((('b', 'v', 'd'), 3), l)
        self.assertIn((('a',), 1), l)
        # overwrite previous elements
        tree['b']['c'] = 5
        l = list(tree)
        self.assertEquals(len(l), 3)
        self.assertIn((('b', 'c'), 5), l)
        self.assertIn((('b', 'v', 'd'), 3), l)
        self.assertIn((('a',), 1), l)

    def test_paths(self):
        tree = Tree()
        tree['b']['c']['e'] = 4
        tree['b']['v']['d'] = 3
        tree['a'] = 1
        expected = {('b', 'c', 'e'): 4, ('b', 'v', 'd'): 3, ('a',): 1}
        self.assertDictEqual(expected, tree.paths())

    def test_pickle_dict(self):
        d = {'a': 1, 'b': 2}
        tree = Tree(**d)
        self.assertEqual(tree['a'], 1)
        self.assertEqual(tree['b'], 2)
        f = BytesIO()
        pickle.dump(tree, f)
        f.seek(0)
        tree_2 = pickle.load(f)
        self.assertEquals(type(tree), type(tree_2))
        self.assertEquals(tree, tree_2)
        self.assertEqual(tree_2['a'], 1)
        self.assertEqual(tree_2['b'], 2)
        self.assertIsInstance(tree, Tree)
        self.assertIsInstance(tree_2, Tree)

    def test_pickle_empty(self):
        tree = Tree()
        f = BytesIO()
        pickle.dump(tree, f)
        f.seek(0)
        tree_2 = pickle.load(f)
        self.assertEquals(type(tree), type(tree_2))
        self.assertEquals(tree, tree_2)
        self.assertIsInstance(tree, Tree)
        self.assertIsInstance(tree_2, Tree)

    def test_pickle(self):
        tree = Tree()
        tree[1][2][3] = '123'
        tree[1][2][4] = '124'
        f = BytesIO()
        pickle.dump(tree, f)
        f.seek(0)
        tree_2 = pickle.load(f)
        self.assertEquals(type(tree), type(tree_2))
        self.assertEquals(tree, tree_2)
        self.assertEquals(tree[1][2][3], '123')
        self.assertEquals(tree_2[1][2][3], '123')
        self.assertIsInstance(tree, Tree)
        self.assertIsInstance(tree_2, Tree)

    def test_str(self):
        tree = Tree({'a': {'b': 'a'}, 'b': 'c', 'd': {'b': 'c'}})
        self.assertEqual(eval(str(tree)), tree)

    def test_dict_1(self):
        d = {'a': 1, 'b': 2}
        tree = Tree(d)
        self.assertEqual(d, tree.dict())

    def test_dict_2(self):
        d = {'a': {'b': 'a'}, 'b': 'c', 'd': {'b': 'c'}}
        tree = Tree(d)
        self.assertEqual(d, tree.dict())

    def test_dict_3(self):
        d = {'a': {'b': [1, 2, 'v']}, 'b': 'c', 'd': {'b': 4}}
        tree = Tree(d)
        self.assertEqual(d, tree.dict())

    def test_match(self):
        t = {'a': {'b': 1}, 'c': 2, 'd': {'e': 3}}
        pos_match_equal = {'a': {'b': 1}, 'c': 2, 'd': {'e': 3}}
        pos_match_subset = {'a': {'b': 1}, 'd': {'e': 3}}
        neg_match_diff = {'a': {'b': 2}, 'c': 2, 'd': {'e': 3}}
        neg_match_superset = {'a': {'b': 1}, 'c': 2, 'd': {'e': 3}, 'f': 3}
        tree = Tree(t)
        self.assertTrue(tree.match(pos_match_equal))
        self.assertTrue(tree.match(pos_match_subset))
        self.assertFalse(tree.match(neg_match_diff))
        self.assertFalse(tree.match(neg_match_superset))

    def test_match_empty_tree(self):
        tree = Tree()
        self.assertFalse(tree.match({'a': 1}))
