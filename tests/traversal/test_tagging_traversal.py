from itertools import groupby

import pytest

from bw_graph_tools import NewNodeEachVisitGraphTraversal
from bw_graph_tools.graph_traversal import (
    NewNodeEachVisitTaggedGraphTraversal,
    SupplyChainTraversalSettings,
    TaggedSupplyChainTraversalSettings,
)
from bw_graph_tools.graph_traversal.graph_objects import GroupedNodes, Node, Edge
import bw2data as bd

from bw_graph_tools.graph_traversal.utils import Counter


def get_default_graph(lca, tags):
    return NewNodeEachVisitTaggedGraphTraversal(
        lca=lca,
        settings=TaggedSupplyChainTraversalSettings(cutoff=0.001, max_calc=10, tags=tags),
    )


def get_untagged_new_graph(lca):
    return NewNodeEachVisitGraphTraversal(
        lca=lca, settings=SupplyChainTraversalSettings(cutoff=0.001, max_calc=10)
    )


@pytest.fixture
def graph(sample_database_with_tagged_products):
    g = get_default_graph(sample_database_with_tagged_products, ["test"])
    yield g


class Faker:
    @staticmethod
    def generate_list_from_bwdata_names(items):
        nodes = []
        count = Counter()
        for item in items:
            activity = bd.get_node(name=item)
            n = Node(
                unique_id=next(count),
                activity_datapackage_id=activity["id"],
                activity_index=-1,
                reference_product_datapackage_id=-1,
                reference_product_index=-1,
                reference_product_production_amount=1,
                supply_amount=1,
                depth=0,
                cumulative_score=1,
                direct_emissions_score=1,
            )
            nodes.append(n)
        return nodes

    @staticmethod
    def generate_edges_from_tuples(items):
        return [
            Edge(
                consumer_index=left,
                consumer_unique_id=left,
                producer_index=right,
                producer_unique_id=right,
                product_index=right,
                amount=1,
            )
            for left, right in items
        ]


class TestNewNodeTaggingTraversal:
    @pytest.mark.parametrize(
        "children, tags, expected",
        # children: list of nodes by names
        # tags: list of tags
        # expected: dictionary of nodes by tags
        [
            [
                list("3456"),
                ["test"],
                {
                    "": [],
                    "test: group-a": list("45"),
                    "test: group-b": list("36"),
                },
            ],
            [
                list("3456"),
                ["invalid-tag"],
                {
                    "": list("3456"),
                },
            ],
            [
                list("3456"),
                ["test", "invalid-second"],
                {
                    "": [],
                    "test: group-a,invalid-second: ": list("45"),
                    "test: group-b,invalid-second: ": list("36"),
                },
            ],
            [
                list("3456"),
                ["test", "second"],
                {
                    "": [],
                    "test: group-a,second: ": list("45"),
                    "test: group-b,second: ": list("3"),
                    "test: group-b,second: 1": list("6"),
                },
            ],
        ],
        ids=[
            "group by test",
            "group by invalid-tag",
            "group by test and invalid-second",
            "group by test and second",
        ],
    )
    def test_group_nodes_by_tags(self, children, tags, expected, tagged_data):
        results = NewNodeEachVisitTaggedGraphTraversal.group_nodes_by_tags(
            Faker.generate_list_from_bwdata_names(children), tags
        )
        expected_results = {
            k: Faker.generate_list_from_bwdata_names(v) for k, v in expected.items()
        }

        def transform(v):
            return [n.activity_datapackage_id for n in v]

        left = {k: transform(v) for k, v in results.items()}
        right = {k: transform(v) for k, v in expected_results.items()}
        assert left == right, "Expecting the same results"

    @pytest.mark.parametrize(
        "edges, expected",
        [
            [
                [(1, 2), (2, 3)],
                {
                    2: {
                        3,
                    }
                },
            ],
            [
                [(1, 2), (2, 3), (2, 4), (2, 5), (2, 6)],
                {
                    2: {
                        3,
                        4,
                        5,
                        6,
                    }
                },
            ],
            [
                [(1, 2), (2, 3), (3, 4), (4, 5), (5, 6)],
                {5: {6}},
            ],
            [
                [(1, 2), (2, 3), (2, 4), (4, 5)],
                {2: {3}, 4: {5}},
            ],
        ],
    )
    def test_group_leaf_nodes_by_parent(self, edges, expected):
        results = NewNodeEachVisitTaggedGraphTraversal.group_leaf_nodes_by_parent(
            Faker.generate_edges_from_tuples(edges)
        )
        assert dict(results) == expected, "Expecting the same results"

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
        groupby_tag = groupby(sorted(grouped_nodes, key=keyfunc), key=keyfunc)
        groups = {label: list(group) for label, group in groupby_tag}
        # there should be four groups
        assert len(grouped_nodes) == 4
        assert len(groups) == 2
        assert len(groups["test: group-a"]) == 2
        assert len(groups["test: group-b"]) == 2

        assert len(groups["test: group-a"][0].nodes) == 1
        assert len(groups["test: group-b"][0].nodes) == 3
