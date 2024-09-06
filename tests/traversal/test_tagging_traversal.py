from itertools import groupby

import pytest

from bw_graph_tools import NewNodeEachVisitGraphTraversal
from bw_graph_tools.graph_traversal import NewNodeEachVisitTaggedGraphTraversal, TaggedSupplyChainTraversalSettings, \
    SupplyChainTraversalSettings
from bw_graph_tools.graph_traversal.graph_objects import GroupedNodes


def get_default_graph(lca, tags):
    return NewNodeEachVisitTaggedGraphTraversal(
        lca=lca,
        settings=TaggedSupplyChainTraversalSettings(
            cutoff=0.001,
            max_calc=10,
            tags=tags
        )
    )


def get_untagged_new_graph(lca):
    return NewNodeEachVisitGraphTraversal(
        lca=lca,
        settings=SupplyChainTraversalSettings(
            cutoff=0.001,
            max_calc=10
        )
    )


@pytest.fixture
def graph(sample_database_with_tagged_products):
    g = get_default_graph(sample_database_with_tagged_products, ['test'])
    yield g


class TestNewNodeTaggingTraversal:
    def test_untagged_traversal(self, sample_database_with_tagged_products):
        graph = get_default_graph(sample_database_with_tagged_products, [])
        duplicate_graph = get_untagged_new_graph(sample_database_with_tagged_products)
        graph.traverse()
        duplicate_graph.traverse()
        assert graph.nodes == duplicate_graph.nodes
        assert graph.edges == duplicate_graph.edges

    def test_tagged_traversal(self, graph, sample_database_with_tagged_products):
        untagged_graph = get_untagged_new_graph(sample_database_with_tagged_products)
        untagged_graph.traverse()
        graph.traverse()
        assert len(graph.nodes) != len(untagged_graph.nodes)
        assert len(graph.nodes) == 9
        assert len(untagged_graph.nodes) == 13

        grouped_nodes = [node for node in graph.nodes.values() if isinstance(node, GroupedNodes)]
        keyfunc = lambda n: n.label
        groupby_tag = groupby(
            sorted(grouped_nodes, key=keyfunc),
            key=keyfunc
        )
        groups = {label: list(group) for label, group in groupby_tag}
        # there should be four groups
        assert len(grouped_nodes) == 4
        assert len(groups) == 2
        assert len(groups['test: group-a']) == 2
        assert len(groups['test: group-b']) == 2

        assert len(groups['test: group-a'][0].nodes) == 1
        assert len(groups['test: group-b'][0].nodes) == 3
