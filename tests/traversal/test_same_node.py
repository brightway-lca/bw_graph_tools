import pytest

from bw_graph_tools.graph_traversal import (
    SameNodeEachVisitGraphTraversal,
    SupplyChainTraversalSettings,
)
from bw_graph_tools.graph_traversal.base import GraphTraversalException


def get_default_graph(lca):
    return SameNodeEachVisitGraphTraversal(
        lca=lca, settings=SupplyChainTraversalSettings(cutoff=0.001, max_calc=3)
    )


@pytest.fixture
def graph(sample_database_with_products):
    g = get_default_graph(sample_database_with_products)
    yield g


class TestSameNodeTraversal:
    def test_traversal_from_root_node(self, graph):
        graph.traverse(max_depth=1)
        assert len(graph.nodes) == 2
        assert (
            graph.traverse_from_node(node=graph._root_node, max_depth=1) is False
        ), "Expecting that root node was already visiting"

    @pytest.mark.parametrize("max_depth", [1, 2, 3])
    def test_traversal_from_node_with_depth(self, graph, max_depth):
        graph.traverse(max_depth=max_depth)
        for _, node in graph.nodes.items():
            if node.depth >= max_depth:
                continue
            assert (
                graph.traverse_from_node(node=node, max_depth=node.depth + 1) is False
            ), f"Expected node with depth <= {max_depth} was already visited"

    def test_traversal_same_with_full_depth(self, graph):
        duplicate_graph = get_default_graph(graph.lca)
        duplicate_graph.traverse(max_depth=100)

        graph.traverse(max_depth=1)
        terminal_nodes = [node for _, node in graph.nodes.items() if node.terminal]
        graph.traverse(terminal_nodes, max_depth=100)

        assert graph.nodes == duplicate_graph.nodes
        assert graph.edges == duplicate_graph.edges

    def test_traversal_with_same_node(self, graph):
        graph.traverse(max_depth=1)
        with pytest.raises(GraphTraversalException):
            graph.traverse(max_depth=100)

        graph.traverse(nodes=[graph.nodes[0]], max_depth=2)
        with pytest.raises(GraphTraversalException):
            graph.traverse(nodes=[graph.nodes[0]], max_depth=2)

    def test_root_node_visited(self, graph):
        assert -1 not in graph.visited_nodes
        graph.traverse()
        assert -1 in graph.visited_nodes
