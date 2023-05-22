import numpy as np
from bw2calc import LCA
from bw2data import Database, Method
from bw2data.tests import bw2test

from bw_graph_tools import NewNodeEachVisitGraphTraversal
from bw_graph_tools.testing import node_equal_dict, flow_equal_dict, edge_equal_dict


@bw2test
def test_marc_van_der_meide_bug():
    """Bug reported by Marc van der Meide with previous implementation."""
    Database("bio").write(
        {
            ("bio", "co2"): {
                "type": "emission",
                "name": "co2",
                "exchanges": [],
            },
        }
    )
    Database("t").write(
        {
            ("t", "coal mining"): {
                "name": "coal mining",
                "exchanges": [
                    {
                        "input": ("bio", "co2"),
                        "amount": 0.1,
                        "type": "biosphere",
                    },
                    {
                        "input": ("t", "hot-rolling"),
                        "amount": 0.1,
                        "type": "technosphere",
                    },
                    {
                        "input": ("t", "coal mining"),
                        "amount": 1,
                        "type": "production",
                    },
                ],
            },
            ("t", "electricity production"): {
                "name": "electricity production",
                "exchanges": [
                    {
                        "input": ("bio", "co2"),
                        "amount": 1,
                        "type": "biosphere",
                    },
                    {
                        "input": ("t", "coal mining"),
                        "amount": 1,
                        "type": "technosphere",
                    },
                    {
                        "input": ("t", "electricity production"),
                        "amount": 1,
                        "type": "production",
                    },
                ],
            },
            ("t", "hot-rolling"): {
                "name": "hot-rolling",
                "exchanges": [
                    {
                        "input": ("bio", "co2"),
                        "amount": 0.1,
                        "type": "biosphere",
                    },
                    {
                        "input": ("t", "steel smelting"),
                        "amount": 1,
                        "type": "technosphere",
                    },
                    {
                        "input": ("t", "electricity production"),
                        "amount": 0.5,
                        "type": "technosphere",
                    },
                    {
                        "input": ("t", "hot-rolling"),
                        "amount": 1,
                        "type": "production",
                    },
                ],
            },
            ("t", "iron ore mining"): {
                "name": "iron ore mining",
                "exchanges": [
                    {
                        "input": ("t", "electricity production"),
                        "amount": 0.5,
                        "type": "technosphere",
                    },
                    {
                        "input": ("t", "hot-rolling"),
                        "amount": 0.1,
                        "type": "technosphere",
                    },
                    {
                        "input": ("t", "iron ore mining"),
                        "amount": 1,
                        "type": "production",
                    },
                ],
            },
            ("t", "steel smelting"): {
                "name": "steel smelting",
                "exchanges": [
                    {
                        "input": ("bio", "co2"),
                        "amount": 1.1,
                        "type": "biosphere",
                    },
                    {
                        "input": ("t", "coal mining"),
                        "amount": 1,
                        "type": "technosphere",
                    },
                    {
                        "input": ("t", "electricity production"),
                        "amount": 0.5,
                        "type": "technosphere",
                    },
                    {
                        "input": ("t", "iron ore mining"),
                        "amount": 2,
                        "type": "technosphere",
                    },
                    {
                        "input": ("t", "steel smelting"),
                        "amount": 1,
                        "type": "production",
                    },
                ],
            },
        }
    )
    Method(("test",)).write(
        [
            (("bio", "co2"), 1),
        ]
    )
    lca = LCA({("t", "hot-rolling"): 1}, ("test",))
    lca.lci()
    lca.lcia()

    assert np.allclose(lca.score, 7)

    gtr = NewNodeEachVisitGraphTraversal.calculate(
        lca_object=lca,
        max_calc=10000,
        cutoff=1e-12,
    )
    _, flows, nodes = gtr["edges"], gtr["flows"], gtr["nodes"]

    assert 6 < sum(flow.score for flow in flows) < 7
    assert 6.5 < sum(node.direct_emissions_score for node in nodes.values()) < 7
