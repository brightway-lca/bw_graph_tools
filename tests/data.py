import pytest
from bw2calc import LCA
from bw2data import Database, Method


@pytest.fixture
def sample_database_with_products():
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

    yield lca


@pytest.fixture
def sample_database_with_tagged_products():
    Database("bio").write(
        {
            ("bio", "a"): {
                "type": "emission",
                "name": "a",
                "exchanges": [],
                "tags": {
                    "test": "group-a",
                },
            },
            ("bio", "b"): {
                "type": "emission",
                "name": "b",
                "exchanges": [],
                "tags": {
                    "test": "group-a",
                },
            },
            ("bio", "c"): {
                "type": "emission",
                "name": "c",
                "exchanges": [],
                "tags": {
                    "test": "group-b",
                },
            },
            ("bio", "d"): {
                "type": "emission",
                "name": "d",
                "exchanges": [],
                "tags": {
                    "test": "group-b",
                },
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
                    {"input": ("t", "3"), "amount": 4, "type": "technosphere"},
                    {"input": ("t", "5"), "amount": 1, "type": "technosphere"},
                    {"input": ("t", "6"), "amount": 1, "type": "technosphere"},
                    {"input": ("t", "7"), "amount": 1, "type": "technosphere"},
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
                "tags": {
                    "test": "group-b",
                },
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
                "tags": {
                    "test": "group-a",
                },
            },
            ("t", "5"): {
                "name": "5",
                "exchanges": [
                    {
                        "input": ("bio", "c"),
                        "amount": 0.02,
                        "type": "biosphere",
                    },
                    {
                        "input": ("t", "5"),
                        "amount": 1,
                        "type": "production",
                    },
                ],
                "tags": {
                    "test": "group-a",
                },
            },
            ("t", "6"): {
                "name": "6",
                "exchanges": [
                    {
                        "input": ("bio", "d"),
                        "amount": 0.4,
                        "type": "biosphere",
                    },
                    {
                        "input": ("t", "6"),
                        "amount": 1,
                        "type": "production",
                    },
                ],
                "tags": {
                    "test": "group-b",
                },
            },
            ("t", "7"): {
                "name": "7",
                "exchanges": [
                    {
                        "input": ("bio", "c"),
                        "amount": 0.2,
                        "type": "biosphere",
                    },
                    {
                        "input": ("bio", "d"),
                        "amount": 0.2,
                        "type": "biosphere",
                    },
                    {
                        "input": ("t", "7"),
                        "amount": 1,
                        "type": "production",
                    },
                ],
                "tags": {
                    "test": "group-b",
                },
            },
        }
    )
    Method(("test",)).write(
        [
            (("bio", "a"), 2),
            (("bio", "b"), 2),
            (("bio", "c"), 2),
            (("bio", "d"), 2),
        ]
    )
    lca = LCA({("t", "2"): 8}, ("test",))
    lca.lci()
    lca.lcia()

    yield lca
