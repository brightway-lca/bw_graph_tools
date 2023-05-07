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
