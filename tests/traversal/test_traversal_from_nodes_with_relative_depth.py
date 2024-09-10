import numpy as np
from bw2calc import LCA
from bw2data import Database, Method, get_node
from bw2data.tests import bw2test

from bw_graph_tools import GraphTraversalSettings, NewNodeEachVisitGraphTraversal
from bw_graph_tools.testing import edge_equal_dict, flow_equal_dict, node_equal_dict


@bw2test
def test_basic_traversal():
    Database("bio").write(
        {
            ("bio", "a"): {
                "type": "emission",
                "name": "a",
                "exchanges": [],
            },
            ("bio", "b"): {
                "type": "emission",
                "name": "b",
                "exchanges": [],
            },
        }
    )
    Database("t").write(
        {
            ("t", "1"): {
                "name": "1",
                "exchanges": [
                    {
                        "input": ("bio", "a"),
                        "amount": 0.5,
                        "type": "biosphere",
                    },
                    {
                        "input": ("t", "2"),
                        "amount": 1,
                        "type": "technosphere",
                    },
                    {
                        "input": ("t", "1"),
                        "amount": 2,
                        "type": "production",
                    },
                ],
            },
            ("t", "2"): {
                "name": "2",
                "exchanges": [
                    {
                        "input": ("bio", "a"),
                        "amount": 1,
                        "type": "biosphere",
                    },
                    {
                        "input": ("bio", "b"),
                        "amount": 0.02,
                        "type": "biosphere",
                    },
                    {
                        "input": ("t", "1"),
                        "amount": 2,
                        "type": "technosphere",
                    },
                    {
                        "input": ("t", "2"),
                        "amount": 2,
                        "type": "production",
                    },
                    {
                        "input": ("t", "3"),
                        "amount": 4,
                        "type": "technosphere",
                    },
                ],
            },
            ("t", "3"): {
                "name": "3",
                "exchanges": [
                    {
                        "input": ("bio", "b"),
                        "amount": 0.01,
                        "type": "biosphere",
                    },
                    {
                        "input": ("t", "3"),
                        "amount": 1,
                        "type": "production",
                    },
                ],
            },
            ("t", "4"): {
                "name": "4",
                "exchanges": [
                    {
                        "input": ("bio", "b"),
                        "amount": 0.02,
                        "type": "biosphere",
                    },
                    {
                        "input": ("t", "4"),
                        "amount": 1,
                        "type": "production",
                    },
                ],
            },
        }
    )
    Method(("test",)).write(
        [
            (("bio", "a"), 2),
            (("bio", "b"), 2),
        ]
    )
    lca = LCA({("t", "2"): 8}, ("test",))
    lca.lci()
    lca.lcia()

    assert np.allclose(lca.score, 24.96)

    gtr = NewNodeEachVisitGraphTraversal(
        lca=lca, settings=GraphTraversalSettings(max_depth=2, cutoff=0.001)
    )
    gtr.traverse()

    # New traversal
    gtr.traverse(
        nodes=[gtr.nodes[1]],  # ("t", "1")
        depth=2,
        reset_results=True,
    )

    assert len(gtr.edges) == 3
    assert len(gtr.nodes) == 4
    assert len(gtr.flows) == 5

    one = get_node(code="1").id
    two = get_node(code="2").id
    three = get_node(code="3").id
    aaa = get_node(code="a").id
    bbb = get_node(code="b").id

    assert gtr.nodes[1].activity_datapackage_id == one

    expected_flows = [
        {
            "activity_id": one,
            "activity_index": lca.dicts.activity[one],
            "activity_unique_id": 1,
            "amount": 2.0,
            "flow_datapackage_id": aaa,
            "flow_index": lca.dicts.biosphere[aaa],
            "score": 4.0,
        },
        {
            "activity_id": two,
            "activity_index": lca.dicts.activity[two],
            "activity_unique_id": 3,
            "amount": 2.0,
            "flow_datapackage_id": aaa,
            "flow_index": lca.dicts.biosphere[aaa],
            "score": 4.0,
        },
        {
            "activity_id": one,
            "activity_index": lca.dicts.activity[one],
            "activity_unique_id": 4,
            "amount": 1.0,
            "flow_datapackage_id": aaa,
            "flow_index": lca.dicts.biosphere[aaa],
            "score": 2.0,
        },
        {
            "activity_id": three,
            "activity_index": lca.dicts.activity[three],
            "activity_unique_id": 5,
            "amount": 0.08,
            "flow_datapackage_id": bbb,
            "flow_index": lca.dicts.biosphere[bbb],
            "score": 0.16,
        },
        {
            "activity_id": two,
            "activity_index": lca.dicts.activity[two],
            "activity_unique_id": 3,
            "amount": 0.04,
            "flow_datapackage_id": bbb,
            "flow_index": lca.dicts.biosphere[bbb],
            "score": 0.08,
        },
    ]
    for a, b in zip(gtr.flows, expected_flows):
        flow_equal_dict(a, b)

    expected_edges = [
        {
            "amount": 4,
            "consumer_index": lca.dicts.activity[one],
            "consumer_unique_id": 1,
            "producer_index": lca.dicts.activity[two],
            "producer_unique_id": 3,
            "product_index": lca.dicts.product[two],
        },
        {
            "amount": 4,
            "consumer_index": lca.dicts.activity[two],
            "consumer_unique_id": 3,
            "producer_index": lca.dicts.activity[one],
            "producer_unique_id": 4,
            "product_index": lca.dicts.product[one],
        },
        {
            "amount": 8,
            "consumer_index": lca.dicts.activity[two],
            "consumer_unique_id": 3,
            "producer_index": lca.dicts.activity[three],
            "producer_unique_id": 5,
            "product_index": lca.dicts.product[three],
        },
    ]
    for a, b in zip(gtr.edges, expected_edges):
        edge_equal_dict(a, b)
