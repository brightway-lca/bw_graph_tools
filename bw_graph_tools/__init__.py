__all__ = (
    "__version__",
    "to_normalized_adjacency_matrix",
    "get_path_from_matrix",
    "path_as_brightway_objects",
    "GraphTraversal",
)

from .graph_traversal_utils import get_path_from_matrix, path_as_brightway_objects
from .matrix_utils import to_normalized_adjacency_matrix
from .utils import get_version_tuple

try:
    from .graph_traversal import GraphTraversal
except ImportError:
    print("Graph traversal class not imported; it relies on `bw2calc` library.")


__version__ = get_version_tuple()
