import numpy as np
from bw2calc import LCA
from bw2data import Database, Method
from bw2data.tests import bw2test

from bw_graph_tools import NewNodeEachVisitGraphTraversal
from bw_graph_tools.testing import node_equal_dict, flow_equal_dict, edge_equal_dict


@bw2test
def test_only_one_node_error_message():
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
        }
    )
    Method(("test",)).write(
        [
            (("bio", "a"), 2),
        ]
    )
    lca = LCA({("t", "1"): 1}, ("test",))
    lca.lci()
    lca.lcia()

    assert np.array_equal([[2]], lca.technosphere_matrix.todense())
    assert np.allclose(lca.score, 0.5)

    gtr = NewNodeEachVisitGraphTraversal.calculate(
        lca_object=lca,
        cutoff=0.001,
    )
    edges, flows, nodes = gtr["edges"], gtr["flows"], gtr["nodes"]

    assert len(edges) == 1
    assert len(flows) == 1
    assert len(nodes) == 2

    expected_flows = [
        {
            "flow_datapackage_id": 1,  # From SQLite, starts at 1
            "flow_index": 0,
            "activity_unique_id": 0,  # Start with activity 2, visit first
            "activity_id": 2,
            "activity_index": 0,
            "amount": 0.25,
            "score": 0.5,
        },
    ]
    for a, b in zip(flows, expected_flows):
        flow_equal_dict(a, b)
