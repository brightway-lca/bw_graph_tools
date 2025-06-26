import numpy as np
from bw2calc import LCA
from bw2data import Database, Method, get_node
from bw2data.tests import bw2test

from bw_graph_tools import NewNodeEachVisitGraphTraversal
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

    a_id = get_node(code="a").id
    b_id = get_node(code="b").id
    t1_id = get_node(code="1").id
    t2_id = get_node(code="2").id
    t3_id = get_node(code="3").id

    assert np.allclose(lca.score, 24.96)

    gtr = NewNodeEachVisitGraphTraversal.calculate(
        lca_object=lca,
        max_depth=2,
        cutoff=0.001,
    )
    edges, flows, nodes = gtr["edges"], gtr["flows"], gtr["nodes"]

    assert len(edges) == 3
    assert len(nodes) == 4
    assert len(flows) == 4

    expected_flows = [
        {
            "activity_id": t2_id,
            "activity_index": 1,
            "activity_unique_id": 0,
            "amount": 4.0,
            "flow_datapackage_id": a_id,
            "flow_index": 0,
            "score": 8.0,
        },
        {
            "activity_id": t1_id,
            "activity_index": 0,
            "activity_unique_id": 1,
            "amount": 2.0,
            "flow_datapackage_id": a_id,
            "flow_index": 0,
            "score": 4.0,
        },
        {
            "activity_id": t3_id,
            "activity_index": 2,
            "activity_unique_id": 2,
            "amount": 0.16,
            "flow_datapackage_id": b_id,
            "flow_index": 1,
            "score": 0.32,
        },
        {
            "activity_id": t2_id,
            "activity_index": 1,
            "activity_unique_id": 0,
            "amount": 0.08,
            "flow_datapackage_id": b_id,
            "flow_index": 1,
            "score": 0.16,
        },
    ]
    for a, b in zip(flows, expected_flows):
        flow_equal_dict(a, b)

    expected_edges = [
        {
            "amount": 8,
            "consumer_index": -1,
            "consumer_unique_id": -1,
            "producer_index": 1,
            "producer_unique_id": 0,
            "product_index": 1,
        },
        {
            "amount": 8.0,
            "consumer_index": 1,
            "consumer_unique_id": 0,
            "producer_index": 0,
            "producer_unique_id": 1,
            "product_index": 0,
        },
        {
            "amount": 16.0,
            "consumer_index": 1,
            "consumer_unique_id": 0,
            "producer_index": 2,
            "producer_unique_id": 2,
            "product_index": 2,
        },
    ]

    for a, b in zip(edges, expected_edges):
        edge_equal_dict(a, b)

    expected_nodes = [
        {
            "activity_datapackage_id": -1,
            "activity_index": -1,
            "cumulative_score": 24.96,
            "direct_emissions_score": 0.0,
            "direct_emissions_score_outside_specific_flows": 0.0,
            "reference_product_datapackage_id": -1,
            "reference_product_index": -1,
            "depth": 0,
            "reference_product_production_amount": 1.0,
            "remaining_cumulative_score_outside_specific_flows": 0.0,
            "supply_amount": 1.0,
            "terminal": False,
            "unique_id": -1,
        },
        {
            "activity_datapackage_id": t2_id,
            "activity_index": 1,
            "cumulative_score": 24.96,
            "direct_emissions_score": 8.16,
            "direct_emissions_score_outside_specific_flows": 0.0,
            "reference_product_datapackage_id": t2_id,
            "reference_product_index": 1,
            "depth": 1,
            "reference_product_production_amount": 2.0,
            "remaining_cumulative_score_outside_specific_flows": 16.8,
            "supply_amount": 4.0,
            "terminal": False,
            "unique_id": 0,
        },
        {
            "activity_datapackage_id": t1_id,
            "activity_index": 0,
            "cumulative_score": 16.48,
            "direct_emissions_score": 4.0,
            "direct_emissions_score_outside_specific_flows": 0.0,
            "reference_product_datapackage_id": t1_id,
            "reference_product_index": 0,
            "depth": 2,
            "reference_product_production_amount": 2.0,
            "remaining_cumulative_score_outside_specific_flows": 12.48,
            "supply_amount": 4.0,
            "terminal": False,
            "unique_id": 1,
        },
        {
            "activity_datapackage_id": t3_id,
            "activity_index": 2,
            "cumulative_score": 0.32,
            "direct_emissions_score": 0.32,
            "direct_emissions_score_outside_specific_flows": 0.0,
            "reference_product_datapackage_id": t3_id,
            "reference_product_index": 2,
            "depth": 2,
            "reference_product_production_amount": 1.0,
            "remaining_cumulative_score_outside_specific_flows": 0.0,
            "supply_amount": 16.0,
            "terminal": True,
            "unique_id": 2,
        },
    ]
    for a in expected_nodes:
        node_equal_dict(nodes[a["unique_id"]], a)
