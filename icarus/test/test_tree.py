from io import BytesIO
try:
    # Python 2
    import cPickle as pickle
except ImportError:
    # Python 3
    import pickle

from icarus.util import Tree


class TestTree(object):

    def test_init_from_tree(self):
        t = Tree({'a': 1, 'b': 2})
        tree = Tree(t)
        assert tree.getval(['a']) == 1
        assert tree.getval(['b']) == 2
        assert isinstance(tree, Tree)

    def test_init_from_dict(self):
        tree = Tree({'a': 1, 'b': 2})
        assert tree.getval(['a']) == 1
        assert tree.getval(['b']) == 2
        assert isinstance(tree, Tree)

    def test_init_from_kwargs(self):
        tree = Tree(a=1, b=2)
        assert tree.getval(['a']) == 1
        assert tree.getval(['b']) == 2
        assert isinstance(tree, Tree)

    def test_init_from_nested_kwargs(self):
        tree = Tree(a=1, b=dict(c=2))
        assert tree.getval(['a']) == 1
        assert tree.getval(['b', 'c']) == 2
        assert isinstance(tree, Tree)
        assert isinstance(tree['b'], Tree)

    def test_init_from_dict_kwargs(self):
        tree = Tree({'c': 3}, a=1, b=2)
        assert tree.getval(['a']) == 1
        assert tree.getval(['b']) == 2
        assert tree.getval(['c']) == 3
        assert isinstance(tree, Tree)

    def test_init_from_nested_dict(self):
        tree = Tree({'a': {'c': {'e': 1}}, 'b': {'d': 2}})
        assert tree.getval(['a', 'c', 'e']) == 1
        assert tree.getval(['b', 'd']) == 2
        assert isinstance(tree, Tree)
        assert isinstance(tree['a'], Tree)
        assert isinstance(tree['a']['c'], Tree)
        assert isinstance(tree.getval(['a', 'c']), Tree)
        assert isinstance(tree['b'], Tree)

    def test_setitem(self):
        tree = Tree()
        tree['a'] = {'b': 1, 'c': 2}
        assert isinstance(tree, Tree)
        assert isinstance(tree['a'], Tree)
        assert tree.getval(['a', 'b']) == 1
        assert tree.getval(['a', 'c']) == 2

    def test_nested_setitem(self):
        tree = Tree()
        tree['a'] = {'b': {'c': 1}, 'd': 2}
        assert isinstance(tree, Tree)
        assert isinstance(tree['a'], Tree)
        assert isinstance(tree['a']['b'], Tree)
        assert tree.getval(['a', 'b', 'c']) == 1
        assert tree.getval(['a', 'd']) == 2

    def test_update_base(self):
        tree = Tree()
        tree.update({'b': 1, 'c': 2})
        assert isinstance(tree, Tree)
        assert tree.getval(['b']) == 1
        assert tree.getval(['c']) == 2

    def test_update_new_brach(self):
        tree = Tree()
        tree['a'].update({'b': 1, 'c': 2})
        assert isinstance(tree, Tree)
        assert isinstance(tree['a'], Tree)
        assert tree.getval(['a', 'b']) == 1
        assert tree.getval(['a', 'c']) == 2

    def test_nested_update(self):
        tree = Tree()
        tree['a'].update({'b': {'c': 1}, 'd': 2})
        assert isinstance(tree, Tree)
        assert isinstance(tree['a'], Tree)
        assert isinstance(tree['a']['b'], Tree)
        assert tree.getval(['a', 'b', 'c']) == 1
        assert tree.getval(['a', 'd']) == 2

    def test_getset(self):
        tree = Tree()
        tree.setval([1, 2, 3, 4], 5)
        assert tree.getval([1, 2, 3, 4]) == 5

    def test_getval(self):
        tree = Tree()
        tree[1][2][3] = 4
        assert tree.getval([1, 2, 3]) == 4
        assert tree.getval([1, 2])[3] == 4
        assert tree.getval([1])[2][3] == 4

    def test_getval_none(self):
        tree = Tree()
        assert tree.getval([1]) is None
        assert tree.getval([1, 2]) is None
        assert tree.getval([3, 4, 5]) is None

    def test_getval_empty(self):
        tree = Tree()
        _ = tree[1][2][3]
        assert tree.getval([1]) is not None
        assert tree.getval([1, 2]) is not None
        assert tree.getval([1, 2, 3]) is None
        assert tree.getval([1, 2, 3, 4]) is None

    def test_iter(self):
        tree = Tree()
        # add first elements
        tree['b']['c']['e'] = 4
        tree['b']['v']['d'] = 3
        l = list(tree)
        assert len(l) == 2
        assert (('b', 'c', 'e'), 4) in l
        assert (('b', 'v', 'd'), 3) in l
        # add additional element
        tree['a'] = 1
        l = list(tree)
        assert len(l) == 3
        assert (('b', 'c', 'e'), 4) in l
        assert (('b', 'v', 'd'), 3) in l
        assert (('a',), 1) in l
        # overwrite previous elements
        tree['b']['c'] = 5
        l = list(tree)
        assert len(l) == 3
        assert (('b', 'c'), 5) in l
        assert (('b', 'v', 'd'), 3) in l
        assert (('a',), 1) in l

    def test_paths(self):
        tree = Tree()
        tree['b']['c']['e'] = 4
        tree['b']['v']['d'] = 3
        tree['a'] = 1
        expected = {('b', 'c', 'e'): 4, ('b', 'v', 'd'): 3, ('a',): 1}
        assert expected == tree.paths()

    def test_pickle_dict(self):
        d = {'a': 1, 'b': 2}
        tree = Tree(**d)
        assert tree['a'] == 1
        assert tree['b'] == 2
        f = BytesIO()
        pickle.dump(tree, f)
        f.seek(0)
        tree_2 = pickle.load(f)
        assert type(tree) == type(tree_2)
        assert tree == tree_2
        assert tree_2['a'] == 1
        assert tree_2['b'] == 2
        assert isinstance(tree, Tree)
        assert isinstance(tree_2, Tree)

    def test_pickle_empty(self):
        tree = Tree()
        f = BytesIO()
        pickle.dump(tree, f)
        f.seek(0)
        tree_2 = pickle.load(f)
        assert type(tree) == type(tree_2)
        assert tree == tree_2
        assert isinstance(tree, Tree)
        assert isinstance(tree_2, Tree)

    def test_pickle(self):
        tree = Tree()
        tree[1][2][3] = '123'
        tree[1][2][4] = '124'
        f = BytesIO()
        pickle.dump(tree, f)
        f.seek(0)
        tree_2 = pickle.load(f)
        assert type(tree) == type(tree_2)
        assert tree == tree_2
        assert tree[1][2][3] == '123'
        assert tree_2[1][2][3] == '123'
        assert isinstance(tree, Tree)
        assert isinstance(tree_2, Tree)

    def test_str(self):
        tree = Tree({'a': {'b': 'a'}, 'b': 'c', 'd': {'b': 'c'}})
        assert eval(str(tree)) == tree

    def test_dict_1(self):
        d = {'a': 1, 'b': 2}
        tree = Tree(d)
        assert d == tree.dict()

    def test_dict_2(self):
        d = {'a': {'b': 'a'}, 'b': 'c', 'd': {'b': 'c'}}
        tree = Tree(d)
        assert d == tree.dict()

    def test_dict_3(self):
        d = {'a': {'b': [1, 2, 'v']}, 'b': 'c', 'd': {'b': 4}}
        tree = Tree(d)
        assert d == tree.dict()

    def test_match(self):
        t = {'a': {'b': 1}, 'c': 2, 'd': {'e': 3}}
        pos_match_equal = {'a': {'b': 1}, 'c': 2, 'd': {'e': 3}}
        pos_match_subset = {'a': {'b': 1}, 'd': {'e': 3}}
        neg_match_diff = {'a': {'b': 2}, 'c': 2, 'd': {'e': 3}}
        neg_match_superset = {'a': {'b': 1}, 'c': 2, 'd': {'e': 3}, 'f': 3}
        tree = Tree(t)
        assert tree.match(pos_match_equal)
        assert tree.match(pos_match_subset)
        assert not tree.match(neg_match_diff)
        assert not tree.match(neg_match_superset)

    def test_match_empty_tree(self):
        tree = Tree()
        assert not tree.match({'a': 1})
