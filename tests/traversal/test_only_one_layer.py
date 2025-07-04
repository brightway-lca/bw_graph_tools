import numpy as np
from bw2calc import LCA
from bw2data import Database, Method, get_node
from bw2data.tests import bw2test

from bw_graph_tools import NewNodeEachVisitGraphTraversal
from bw_graph_tools.testing import edge_equal_dict, flow_equal_dict, node_equal_dict


@bw2test
def test_basic_nonunitary_production_with_recursion():
    Database("bio").write(
        {
            ("bio", "a"): {
                "type": "emission",
                "name": "a",
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
                        "input": ("t", "2"),
                        "amount": 4,
                        "type": "production",
                    },
                ],
            },
        }
    )
    Method(("test",)).write(
        [
            (("bio", "a"), 2),
        ]
    )
    lca = LCA({("t", "2"): 8, ("t", "1"): 10}, ("test",))
    lca.lci()
    lca.lcia()

    a_id = get_node(code="a").id
    t1_id = get_node(code="1").id
    t2_id = get_node(code="2").id

    assert np.array_equal([[2, 0], [0, 4]], lca.technosphere_matrix.todense())
    assert np.array_equal([5, 2], lca.supply_array)
    assert np.allclose(lca.score, 4 + 5)

    gtr = NewNodeEachVisitGraphTraversal.calculate(
        lca_object=lca,
        cutoff=0.001,
    )
    edges, flows, nodes = gtr["edges"], gtr["flows"], gtr["nodes"]

    assert len(edges) == 2
    assert len(flows) == 2
    assert len(nodes) == 3

    expected_flows = [
        {
            "flow_datapackage_id": a_id,  # From SQLite, starts at 1
            "flow_index": 0,
            "activity_unique_id": 1,  # Start with activity 2, visit first
            "activity_id": t1_id,
            "activity_index": 0,
            "amount": 2.5,
            "score": 5,
        },
        {
            "flow_datapackage_id": a_id,
            "flow_index": 0,
            "activity_unique_id": 0,
            "activity_id": t2_id,
            "activity_index": 1,
            "amount": 2,
            "score": 4,
        },
    ]

    for a, b in zip(flows, expected_flows):
        flow_equal_dict(a, b)

    expected_edges = [
        {
            "consumer_index": -1,
            "consumer_unique_id": -1,
            "producer_index": 1,
            "producer_unique_id": 0,
            "product_index": 1,
            "amount": 8,
        },
        {
            "consumer_index": -1,
            "consumer_unique_id": -1,
            "producer_index": 0,
            "producer_unique_id": 1,
            "product_index": 0,
            "amount": 10,
        },
    ]

    for a, b in zip(edges, expected_edges):
        edge_equal_dict(a, b)

    expected_nodes = [
        {
            "unique_id": -1,
            "activity_datapackage_id": -1,
            "activity_index": -1,
            "reference_product_datapackage_id": -1,
            "reference_product_index": -1,
            "reference_product_production_amount": 1,
            "supply_amount": 1,
            "cumulative_score": 9,
            "direct_emissions_score": 0,
        },
        {
            "unique_id": 0,
            "activity_datapackage_id": t2_id,
            "activity_index": 1,
            "reference_product_datapackage_id": t2_id,
            "reference_product_index": 1,
            "reference_product_production_amount": 4,
            "supply_amount": 2,
            "cumulative_score": 4,
            "direct_emissions_score": 4,
        },
        {
            "unique_id": 1,
            "activity_datapackage_id": t1_id,
            "activity_index": 0,
            "reference_product_datapackage_id": t1_id,
            "reference_product_index": 0,
            "reference_product_production_amount": 2,
            "supply_amount": 5,
            "cumulative_score": 5,
            "direct_emissions_score": 5,
        },
    ]

    for a in expected_nodes:
        node_equal_dict(nodes[a["unique_id"]], a)
