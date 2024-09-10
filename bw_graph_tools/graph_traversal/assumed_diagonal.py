import matrix_utils as mu
import numpy as np

from bw_graph_tools.graph_traversal.new_node_each_visit import NewNodeEachVisitGraphTraversal


class AssumedDiagonalGraphTraversal(NewNodeEachVisitGraphTraversal):
    @classmethod
    def get_production_exchanges(cls, mapped_matrix: mu.MappedMatrix) -> (np.ndarray, np.ndarray):
        """
        Assume production exchanges are always on the diagonal instead of
        examining matrix structure and input data.

        Parameters
        ----------
        mapped_matrix : matrix_utils.MappedMatrix
            A matrix and mapping data (from database ids to matrix indices)
            from the ``matrix_utils`` library. Normally built automatically by
            an ``LCA`` class. Should be the ``technosphere_matrix`` or
            equivalent.

        Returns
        -------
        (numpy.array, numpy.array)
            The matrix row and column indices of the production exchanges.

        """
        length = mapped_matrix.matrix.shape[0]
        return np.arange(length), np.arange(length)
