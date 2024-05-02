:py:mod:`bw_graph_tools.graph_traversal_utils`
==============================================

.. py:module:: bw_graph_tools.graph_traversal_utils


Module Contents
---------------


Functions
~~~~~~~~~

.. autoapisummary::

   bw_graph_tools.graph_traversal_utils.get_path_from_matrix
   bw_graph_tools.graph_traversal_utils.path_as_brightway_objects



Attributes
~~~~~~~~~~

.. autoapisummary::

   bw_graph_tools.graph_traversal_utils.brightway_available


.. py:function:: get_path_from_matrix(matrix: scipy.sparse.spmatrix, source: int, target: int, algorithm: str = 'BF') -> List

   Get the path with the most mass or energetic flow from ``source`` (the function unit) to ``target`` (something deep in the supply chain). Both ``source`` and ``target`` are integer matrix indices.

   ``algorithm`` should be either ``BF`` (Bellman-Ford) or ``J`` (Johnson). Dijkstra is not recommended as we have negative weights.

   Returns a list like ``[source, int, int, int, target]``.


.. py:function:: path_as_brightway_objects(source_node: bw2data.Node, target_node: bw2data.Node, lca: Optional[bw2calc.LCA] = None) -> List[bw2data.Edge]


.. py:data:: brightway_available
   :value: True

   

