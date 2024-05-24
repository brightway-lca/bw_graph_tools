import numpy as np
from bw2calc import LCA
from bw2data import Database, Method
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

    assert np.allclose(lca.score, 24.96)

    gtr = NewNodeEachVisitGraphTraversal.calculate(
        lca_object=lca,
        max_calc=3,
        cutoff=0.001,
    )
    edges, flows, nodes = gtr["edges"], gtr["flows"], gtr["nodes"]

    assert len(edges) == 6
    assert len(nodes) == 7

    expected_flows = [
        {
            "activity_id": 4,
            "activity_index": 1,
            "activity_unique_id": 0,
            "amount": 4.0,
            "flow_datapackage_id": 1,
            "flow_index": 0,
            "score": 8.0,
        },
        {
            "activity_id": 3,
            "activity_index": 0,
            "activity_unique_id": 1,
            "amount": 2.0,
            "flow_datapackage_id": 1,
            "flow_index": 0,
            "score": 4.0,
        },
        {
            "activity_id": 4,
            "activity_index": 1,
            "activity_unique_id": 3,
            "amount": 2.0,
            "flow_datapackage_id": 1,
            "flow_index": 0,
            "score": 4.0,
        },
        {
            "activity_id": 3,
            "activity_index": 0,
            "activity_unique_id": 4,
            "amount": 1.0,
            "flow_datapackage_id": 1,
            "flow_index": 0,
            "score": 2.0,
        },
        {
            "activity_id": 5,
            "activity_index": 2,
            "activity_unique_id": 2,
            "amount": 0.16,
            "flow_datapackage_id": 2,
            "flow_index": 1,
            "score": 0.32,
        },
        {
            "activity_id": 4,
            "activity_index": 1,
            "activity_unique_id": 0,
            "amount": 0.08,
            "flow_datapackage_id": 2,
            "flow_index": 1,
            "score": 0.16,
        },
        {
            "activity_id": 5,
            "activity_index": 2,
            "activity_unique_id": 5,
            "amount": 0.08,
            "flow_datapackage_id": 2,
            "flow_index": 1,
            "score": 0.16,
        },
        {
            "activity_id": 4,
            "activity_index": 1,
            "activity_unique_id": 3,
            "amount": 0.04,
            "flow_datapackage_id": 2,
            "flow_index": 1,
            "score": 0.08,
        },
    ]
    for a, b in zip(flows, expected_flows):
        print(a)
        print(b)
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
        {
            "amount": 4.0,
            "consumer_index": 0,
            "consumer_unique_id": 1,
            "producer_index": 1,
            "producer_unique_id": 3,
            "product_index": 1,
        },
        {
            "amount": 4.0,
            "consumer_index": 1,
            "consumer_unique_id": 3,
            "producer_index": 0,
            "producer_unique_id": 4,
            "product_index": 0,
        },
        {
            "amount": 8.0,
            "consumer_index": 1,
            "consumer_unique_id": 3,
            "producer_index": 2,
            "producer_unique_id": 5,
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
            "reference_product_production_amount": 1.0,
            "remaining_cumulative_score_outside_specific_flows": 0.0,
            "supply_amount": 1.0,
            "terminal": False,
            "unique_id": -1,
        },
        {
            "activity_datapackage_id": 4,
            "activity_index": 1,
            "cumulative_score": 24.96,
            "direct_emissions_score": 8.16,
            "direct_emissions_score_outside_specific_flows": 0.0,
            "reference_product_datapackage_id": 4,
            "reference_product_index": 1,
            "reference_product_production_amount": 2.0,
            "remaining_cumulative_score_outside_specific_flows": 16.8,
            "supply_amount": 4.0,
            "terminal": False,
            "unique_id": 0,
        },
        {
            "activity_datapackage_id": 3,
            "activity_index": 0,
            "cumulative_score": 16.48,
            "direct_emissions_score": 4.0,
            "direct_emissions_score_outside_specific_flows": 0.0,
            "reference_product_datapackage_id": 3,
            "reference_product_index": 0,
            "reference_product_production_amount": 2.0,
            "remaining_cumulative_score_outside_specific_flows": 12.48,
            "supply_amount": 4.0,
            "terminal": False,
            "unique_id": 1,
        },
        {
            "activity_datapackage_id": 5,
            "activity_index": 2,
            "cumulative_score": 0.32,
            "direct_emissions_score": 0.32,
            "direct_emissions_score_outside_specific_flows": 0.0,
            "reference_product_datapackage_id": 5,
            "reference_product_index": 2,
            "reference_product_production_amount": 1.0,
            "remaining_cumulative_score_outside_specific_flows": 0.0,
            "supply_amount": 16.0,
            "terminal": True,
            "unique_id": 2,
        },
        {
            "activity_datapackage_id": 4,
            "activity_index": 1,
            "cumulative_score": 12.48,
            "direct_emissions_score": 4.08,
            "direct_emissions_score_outside_specific_flows": 0.0,
            "reference_product_datapackage_id": 4,
            "reference_product_index": 1,
            "reference_product_production_amount": 2.0,
            "remaining_cumulative_score_outside_specific_flows": 8.4,
            "supply_amount": 2.0,
            "terminal": False,
            "unique_id": 3,
        },
        {
            "activity_datapackage_id": 3,
            "activity_index": 0,
            "cumulative_score": 8.24,
            "direct_emissions_score": 2.0,
            "direct_emissions_score_outside_specific_flows": 0.0,
            "reference_product_datapackage_id": 3,
            "reference_product_index": 0,
            "reference_product_production_amount": 2.0,
            "remaining_cumulative_score_outside_specific_flows": 6.24,
            "supply_amount": 2.0,
            "terminal": True,
            "unique_id": 4,
        },
        {
            "activity_datapackage_id": 5,
            "activity_index": 2,
            "cumulative_score": 0.1599999964237213,
            "direct_emissions_score": 0.1599999964237213,
            "direct_emissions_score_outside_specific_flows": 0.0,
            "reference_product_datapackage_id": 5,
            "reference_product_index": 2,
            "reference_product_production_amount": 1.0,
            "remaining_cumulative_score_outside_specific_flows": 0.0,
            "supply_amount": 8.0,
            "terminal": True,
            "unique_id": 5,
        },
    ]
    for a in expected_nodes:
        node_equal_dict(nodes[a["unique_id"]], a)
