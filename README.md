# bw_graph_tools

[![PyPI](https://img.shields.io/pypi/v/bw_graph_tools.svg)][pypi status]
[![Status](https://img.shields.io/pypi/status/bw_graph_tools.svg)][pypi status]
[![Python Version](https://img.shields.io/pypi/pyversions/bw_graph_tools)][pypi status]
[![License](https://img.shields.io/pypi/l/bw_graph_tools)][license]

[![Read the documentation at https://bw_graph_tools.readthedocs.io/](https://img.shields.io/readthedocs/bw_graph_tools/latest.svg?label=Read%20the%20Docs)][read the docs]
[![Tests](https://github.com/brightway-lca/bw_graph_tools/workflows/Tests/badge.svg)][tests]
[![Codecov](https://codecov.io/gh/brightway-lca/bw_graph_tools/branch/main/graph/badge.svg)][codecov]

[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)][pre-commit]
[![Black](https://img.shields.io/badge/code%20style-black-000000.svg)][black]

[pypi status]: https://pypi.org/project/bw_graph_tools/
[read the docs]: https://bw_graph_tools.readthedocs.io/
[tests]: https://github.com/brightway-lca/bw_graph_tools/actions?workflow=Tests
[codecov]: https://app.codecov.io/gh/brightway-lca/bw_graph_tools
[pre-commit]: https://github.com/pre-commit/pre-commit
[black]: https://github.com/psf/black

## Installation

You can install _bw_graph_tools_ via [pip] from [PyPI]:

```console
$ pip install bw_graph_tools
```

Packages are also on conda at the [channel cmutel](https://anaconda.org/cmutel/bw_graph_tools).

## Usage

`bw_graph_tools` has three main components: A graph traversal class `NewNodeEachVisitGraphTraversal`; a function to guess production exchanges using only `bw_processing` datapackages `guess_production_exchanges`; and a function to find the path from node `A` to node `B` with the largest amount of the reference product of `A`, `get_path_from_matrix` and it's sister `path_as_brightway_objects`.

### `NewNodeEachVisitGraphTraversal`

Normally we construct matrices and solve the resulting set of linear equations to get a life cycle inventory or impact assessment result. The matrix approach is elegant, in that it simultaneously solves all equations and handles cycles in the graph, and much faster than graph traversal. However, in some cases we want to actually traverse the supply chain graph and calculate the individual impact of visiting nodes at that point in the graph. Graph traversal's use cases include:

* Distinguishing between different paths to the same object

* Convolving temporal distributions

If we add temporal information using `bw_temporalis`, then the same node can occur at different times depending on how the temporal dynamics its preceding path. For example:



## Contributing

Contributions are very welcome.
To learn more, see the [Contributor Guide].

## License

Distributed under the terms of the [BSD 3 Clause license][license],
_bw_graph_tools_ is free and open source software.

## Issues

If you encounter any problems,
please [file an issue] along with a detailed description.

## Documentation

1. Install the `sphinx-furo` conda environment from the file `.docs/environment.yml`.
2. Build the documentation locally by running

```
sphinx-autobuild docs _build/html -a -j auto --open-browser
```

<!-- github-only -->

[command-line reference]: https://bw_graph_tools.readthedocs.io/en/latest/usage.html
[license]: https://github.com/brightway-lca/bw_graph_tools/blob/main/LICENSE
[contributor guide]: https://github.com/brightway-lca/bw_graph_tools/blob/main/CONTRIBUTING.md
