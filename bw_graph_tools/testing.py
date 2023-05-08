from numbers import Number
import numpy as np

from . import Node, Edge, Flow


def equal_dict(a: Node | Edge | Flow, b: dict, fields: list[str]):
    for field in fields:
        if field in b:
            if isinstance(b[field], Number):
                assert np.allclose(getattr(a, field), b[field])
            else:
                assert getattr(a, field) == b[field]


def edge_equal_dict(a: Edge, b: dict):
    FIELDS = [
        "consumer_index",
        "consumer_unique_id",
        "producer_index",
        "producer_unique_id",
        "product_index",
        "amount",
    ]
    equal_dict(a, b, FIELDS)


def flow_equal_dict(a: Flow, b: dict):
    FIELDS = [
        "flow_datapackage_id",
        "flow_index",
        "activity_unique_id",
        "activity_id",
        "activity_index",
        "amount",
        "score",
    ]
    equal_dict(a, b, FIELDS)


def node_equal_dict(a: Node, b: dict):
    FIELDS = [
        "unique_id",
        "activity_datapackage_id",
        "activity_index",
        "reference_product_datapackage_id",
        "reference_product_index",
        "reference_product_production_amount",
        "supply_amount",
        "cumulative_score",
        "direct_emissions_score",
    ]
    equal_dict(a, b, FIELDS)
