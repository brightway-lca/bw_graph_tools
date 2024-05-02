:py:mod:`bw_graph_tools.matrix_tools`
=====================================

.. py:module:: bw_graph_tools.matrix_tools


Module Contents
---------------


Functions
~~~~~~~~~

.. autoapisummary::

   bw_graph_tools.matrix_tools.gpe_first_heuristic
   bw_graph_tools.matrix_tools.gpe_second_heuristic
   bw_graph_tools.matrix_tools.gpe_third_heuristic
   bw_graph_tools.matrix_tools.guess_production_exchanges
   bw_graph_tools.matrix_tools.reorder_mapped_matrix
   bw_graph_tools.matrix_tools.to_normalized_adjacency_matrix



.. py:function:: gpe_first_heuristic(mm: matrix_utils.MappedMatrix) -> Tuple[numpy.ndarray, numpy.ndarray]

   Use first heuristic (same input and output ids) to find production exchange indices.

   If we treat activities and products the same, then an exchange with the row and column id
   is definitely a production exchange location. We don't care if there are duplicates (e.g.
   production and some loss), we will return unique pairs.

   If activities have different ids than products, this won't find anything.

   Returns a tuple of numpy integer matrix indices, rows by columns.


.. py:function:: gpe_second_heuristic(mm: matrix_utils.MappedMatrix, row_existing: numpy.ndarray, col_existing: numpy.ndarray) -> Tuple[numpy.ndarray, numpy.ndarray]


.. py:function:: gpe_third_heuristic(mm: matrix_utils.MappedMatrix, row_existing: numpy.ndarray, col_existing: numpy.ndarray) -> Tuple[numpy.ndarray, numpy.ndarray]


.. py:function:: guess_production_exchanges(mm: matrix_utils.MappedMatrix) -> Tuple[numpy.ndarray, numpy.ndarray]

   Try to guess productions exchanges in a mapped technosphere matrix using heuristics from the input data packages.

   Try the following in order per activity (column):

   * Same input and output index
   * Single value where ``flip`` is negative
   * Single positive value

   Raises ``UnclearProductionExchange`` if these conditions are not met for any activity.

   Returns integer arrays of the matrix row and column indices where production exchanges were found.



.. py:function:: reorder_mapped_matrix(matrix: matrix_utils.MappedMatrix) -> scipy.sparse.csr_matrix


.. py:function:: to_normalized_adjacency_matrix(matrix: scipy.sparse.spmatrix, log_transform: bool = True) -> scipy.sparse.csr_matrix

   Take a technosphere matrix constructed with Brightway conventions, and return a normalized adjacency matrix.

   In the adjacency matrix A, `A[i,j]` indicates a directed edge **from** row `i` **to** column `j`. However,
   this is the opposite of what we normally want, which is to find a path from the functional activity to
   somewhere in its supply chain. In a Brightway technosphere matrix, `A[i,j]` means **activity** `j` consumes
   the output of activity `i`. To go down the supply chain, however, we would need to go from ``j`` to ``i``.
   Therefore, we take the transpose of the technosphere matrix.

   Normalization is done to remove the effect of activities which don't produce one unit of their reference product.
   For example, if activity `foo` produces two units of `bar` and consumes two units of `baz`, the weight of the
   `baz` edge should be :math:`2 / 2 = 1`.

   In addition to this normalization, we subtract the diagonal and flip the signs of all matrix values. Flipping
   the sign is needed because we want to use a shortest path algorithm, but actually want the longest path. The
   longest path is the path with the highest weight, i.e. the path where the most consumption occurs on.

   By default, we also take the natural log of the data values. This is because our supply chain is multiplicative,
   not additive, and :math:`a \cdot b = e^{\ln(a) + \ln(b)}`. The idea of using the log was borrowed from `David Richardby on Stack Overflow <https://cs.stackexchange.com/questions/83656/traverse-direct-graph-with-multiplicative-edges>`__.

   Assumes that production amounts are on the diagonal.


