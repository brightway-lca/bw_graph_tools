from bw2data import Database, Method
from bw2data.tests import bw2test
from bw_graph_tools import GraphTraversal
from bw2calc import LCA
import pytest


@pytest.fixture
@bw2test
def simple():
    Database("bio").write({
        ("bio", "a"): {
            'type': 'emission',
            'name': 'a',
            'exchanges': [],
        },
        ("bio", "b"): {
            'type': 'emission',
            'name': 'b',
            'exchanges': [],
        },
    })
    Database("t").write({
        ("t", "1p"): {
            'name': 'foo',
            'type': 'product',
            'exchanges': []
        },
        ("t", "1"): {
            'name': '1',
            'exchanges': [{
                'input': ("t", "1p"),
                'amount': 2,
                'type': 'production',
            }, {
                'input': ("bio", "a"),
                'amount': 2,
                'type': 'biosphere',
            }, {
                'input': ("t", "2p"),
                'amount': 1,
                'type': 'technosphere',
            }]
        },
        ("t", "2p"): {
            'name': 'bar',
            'type': 'product',
            'exchanges': []
        },
        ("t", "2"): {
            'name': '2',
            'exchanges': [{
                'input': ("t", "2p"),
                'amount': 1,
                'type': 'production',
            }, {
                'input': ("bio", "b"),
                'amount': 4,
                'type': 'biosphere',
            }, {
                'input': ("t", "1p"),
                'amount': 1 / 8,
                'type': 'technosphere',
            }]
        },
    })
    Method(("test",)).write([
        (("bio", "a"), 1),
        (("bio", "b"), 8),
    ])


def test_basic_traversal(simple):
    lca = LCA({("t", "1p"): 6, ("t", "2p"): 1}, ("test",))
    lca.lci()
    lca.lcia()

    print(lca.supply_array)

    gtr = GraphTraversal.calculate(
        lca_object=lca,
        max_calc=5,
        cutoff=0.05,
    )
    from pprint import pprint
    pprint(gtr['nodes'])
