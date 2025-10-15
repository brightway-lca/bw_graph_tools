import numpy as np
from bw2calc import LCA
from bw2data import Database, Method, get_node
from bw2data.tests import bw2test

from bw_graph_tools import GraphTraversalSettings, NewNodeEachVisitGraphTraversal
from bw_graph_tools.testing import edge_equal_dict, flow_equal_dict, node_equal_dict


@bw2test
def test_static_activities_appear_but_dont_traverse():
    """
    Test that static activities:
    1. Appear as nodes in the graph
    2. Have edges connecting to them
    3. Don't get traversed further (no children in graph)
    """
    Database("bio").write(
        {
            ("bio", "emission"): {
                "type": "emission",
                "name": "emission",
                "exchanges": [],
            },
        }
    )
    Database("t").write(
        {
            ("t", "root"): {
                "name": "root",
                "exchanges": [
                    {
                        "input": ("bio", "emission"),
                        "amount": 1.0,
                        "type": "biosphere",
                    },
                    {
                        "input": ("t", "static_activity"),
                        "amount": 2,
                        "type": "technosphere",
                    },
                    {
                        "input": ("t", "root"),
                        "amount": 1,
                        "type": "production",
                    },
                ],
            },
            ("t", "static_activity"): {
                "name": "static_activity",
                "exchanges": [
                    {
                        "input": ("bio", "emission"),
                        "amount": 5.0,
                        "type": "biosphere",
                    },
                    {
                        "input": ("t", "child_of_static"),
                        "amount": 3,
                        "type": "technosphere",
                    },
                    {
                        "input": ("t", "static_activity"),
                        "amount": 1,
                        "type": "production",
                    },
                ],
            },
            ("t", "child_of_static"): {
                "name": "child_of_static",
                "exchanges": [
                    {
                        "input": ("bio", "emission"),
                        "amount": 10.0,
                        "type": "biosphere",
                    },
                    {
                        "input": ("t", "child_of_static"),
                        "amount": 1,
                        "type": "production",
                    },
                ],
            },
        }
    )
    Method(("test",)).write([(("bio", "emission"), 1)])

    lca = LCA({("t", "root"): 1}, ("test",))
    lca.lci()
    lca.lcia()

    root_id = get_node(code="root").id
    static_id = get_node(code="static_activity").id
    child_id = get_node(code="child_of_static").id
    emission_id = get_node(code="emission").id

    # Get activity indices for static_activity_indices parameter
    static_activity_index = lca.dicts.activity[static_id]

    # Test WITH static_activity_indices set
    gtr = NewNodeEachVisitGraphTraversal(
        lca=lca,
        settings=GraphTraversalSettings(cutoff=0.001),
        static_activity_indices={static_activity_index},
    )
    gtr.traverse()
    
    edges, flows, nodes = gtr.edges, gtr.flows, gtr.nodes

    # Should have:
    # - Root node (functional unit)
    # - Root activity node
    # - Static activity node
    # Should NOT have:
    # - Child of static activity (because static activity is not traversed)

    assert len(nodes) == 3, f"Expected 3 nodes, got {len(nodes)}"

    # Verify static activity IS in the nodes
    node_activity_ids = [
        n.activity_datapackage_id for n in nodes.values() if n.activity_datapackage_id != -1
    ]
    assert static_id in node_activity_ids, "Static activity should appear in nodes"
    assert (
        child_id not in node_activity_ids
    ), "Child of static activity should NOT appear in nodes"

    # Should have edges connecting to static activity
    assert len(edges) == 2, f"Expected 2 edges, got {len(edges)}"

    # Verify there's an edge to the static activity
    producer_indices = [e.producer_index for e in edges]
    assert static_activity_index in producer_indices, "Should have edge to static activity"


@bw2test
def test_without_static_activities_normal_traversal():
    """Test that when static_activity_indices is empty, traversal proceeds normally."""
    Database("bio").write(
        {
            ("bio", "emission"): {
                "type": "emission",
                "name": "emission",
                "exchanges": [],
            },
        }
    )
    Database("t").write(
        {
            ("t", "root"): {
                "name": "root",
                "exchanges": [
                    {
                        "input": ("bio", "emission"),
                        "amount": 1.0,
                        "type": "biosphere",
                    },
                    {
                        "input": ("t", "middle"),
                        "amount": 2,
                        "type": "technosphere",
                    },
                    {
                        "input": ("t", "root"),
                        "amount": 1,
                        "type": "production",
                    },
                ],
            },
            ("t", "middle"): {
                "name": "middle",
                "exchanges": [
                    {
                        "input": ("bio", "emission"),
                        "amount": 5.0,
                        "type": "biosphere",
                    },
                    {
                        "input": ("t", "child"),
                        "amount": 3,
                        "type": "technosphere",
                    },
                    {
                        "input": ("t", "middle"),
                        "amount": 1,
                        "type": "production",
                    },
                ],
            },
            ("t", "child"): {
                "name": "child",
                "exchanges": [
                    {
                        "input": ("bio", "emission"),
                        "amount": 10.0,
                        "type": "biosphere",
                    },
                    {
                        "input": ("t", "child"),
                        "amount": 1,
                        "type": "production",
                    },
                ],
            },
        }
    )
    Method(("test",)).write([(("bio", "emission"), 1)])

    lca = LCA({("t", "root"): 1}, ("test",))
    lca.lci()
    lca.lcia()

    child_id = get_node(code="child").id

    # Test WITHOUT static_activity_indices (default empty set)
    gtr = NewNodeEachVisitGraphTraversal(
        lca=lca,
        settings=GraphTraversalSettings(cutoff=0.001),
    )
    gtr.traverse()
    
    nodes = gtr.nodes

    # Should traverse all the way through to child
    node_activity_ids = [
        n.activity_datapackage_id for n in nodes.values() if n.activity_datapackage_id != -1
    ]
    assert child_id in node_activity_ids, "Child should appear when no static activities defined"

