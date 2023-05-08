import numpy as np
from bw2calc import LCA
from bw2data import Database, Method
from bw2data.tests import bw2test

from bw_graph_tools import NewNodeEachVisitGraphTraversal
from bw_graph_tools.testing import node_equal_dict, flow_equal_dict, edge_equal_dict


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
                        "input": ("t", "1"),
                        "amount": 2,
                        "type": "technosphere",
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
    lca = LCA({("t", "2"): 8}, ("test",))
    lca.lci()
    lca.lcia()

    assert np.array_equal([[2, -2], [-1, 4]], lca.technosphere_matrix.todense())
    assert np.array_equal([8 / 3, 8 / 3], lca.supply_array)
    assert np.allclose(lca.score, (1 / 3 * 0.5 + 1 / 3 * 1) * 2 * 8)

    gtr = NewNodeEachVisitGraphTraversal.calculate(
        lca_object=lca,
        max_calc=3,
        cutoff=0.001,
    )
    edges, flows, nodes = gtr["edges"], gtr["flows"], gtr["nodes"]

    assert len(edges) == 5  # Initial, three calculations, final not evaluated
    assert len(nodes) == 6

    expected_flows = [
        {
            "flow_datapackage_id": 1,  # From SQLite, starts at 1
            "flow_index": 0,
            "activity_unique_id": 0,  # Start with activity 2, visit first
            "activity_id": 3,
            "activity_index": 1,
            "amount": 2,
            "score": 4,
        },
        {
            "flow_datapackage_id": 1,
            "flow_index": 0,
            "activity_unique_id": 1,
            "activity_id": 2,
            "activity_index": 0,
            "amount": 1,
            "score": 2,
        },
        {
            "flow_datapackage_id": 1,
            "flow_index": 0,
            "activity_unique_id": 2,
            "activity_id": 3,
            "activity_index": 1,
            "amount": 0.5,
            "score": 1,
        },
        {
            "flow_datapackage_id": 1,
            "flow_index": 0,
            "activity_unique_id": 3,
            "activity_id": 2,
            "activity_index": 0,
            "amount": 0.25,
            "score": 0.5,
        },
    ]
    expected_flows.sort(key=lambda x: x["score"], reverse=True)

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
            "consumer_index": 1,
            "consumer_unique_id": 0,
            "producer_index": 0,
            "producer_unique_id": 1,
            "product_index": 0,
            "amount": 4,
        },
        {
            "consumer_index": 0,
            "consumer_unique_id": 1,
            "producer_index": 1,
            "producer_unique_id": 2,
            "product_index": 1,
            "amount": 2,
        },
        {
            "consumer_index": 1,
            "consumer_unique_id": 2,
            "producer_index": 0,
            "producer_unique_id": 3,
            "product_index": 0,
            "amount": 1,
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
            "cumulative_score": 8,
            "direct_emissions_score": 0,
        },
        {
            "unique_id": 0,
            "activity_datapackage_id": 3,
            "activity_index": 1,
            "reference_product_datapackage_id": 3,
            "reference_product_index": 1,
            "reference_product_production_amount": 4,
            "supply_amount": 2,
            "cumulative_score": 8,
            "direct_emissions_score": 4,
        },
        {
            "unique_id": 1,
            "activity_datapackage_id": 2,
            "activity_index": 0,
            "reference_product_datapackage_id": 2,
            "reference_product_index": 0,
            "reference_product_production_amount": 2,
            "supply_amount": 2,
            "cumulative_score": 4,
            "direct_emissions_score": 2,
        },
        {
            "unique_id": 2,
            "activity_datapackage_id": 3,
            "activity_index": 1,
            "reference_product_datapackage_id": 3,
            "reference_product_index": 1,
            "reference_product_production_amount": 4,
            "supply_amount": 0.5,
            "cumulative_score": 2,
            "direct_emissions_score": 1,
        },
        {
            "unique_id": 3,
            "activity_datapackage_id": 2,
            "activity_index": 0,
            "reference_product_datapackage_id": 2,
            "reference_product_index": 0,
            "reference_product_production_amount": 2,
            "supply_amount": 0.5,
            "cumulative_score": 1,
            "direct_emissions_score": 0.5,
        },
        {
            "unique_id": 4,
            "activity_datapackage_id": 3,
            "activity_index": 1,
            "reference_product_datapackage_id": 3,
            "reference_product_index": 1,
            "reference_product_production_amount": 4,
            "supply_amount": 0.125,
            "cumulative_score": 0.5,
            "direct_emissions_score": 0.25,
        },
    ]

    for a in expected_nodes:
        node_equal_dict(nodes[a["unique_id"]], a)
