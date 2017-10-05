"""A decomposition strategy using the definition of components."""


from grids_two import Tiling
from permuta.misc import UnionFind
from itertools import combinations

from comb_spec_searcher import Strategy


def components(tiling, non_interleaving_decomposition=False, **kwargs):
    """
    Yield strategy found by taking components of a tiling.

    Two cells are in the same component if there exists an occurrence using both cells.
    """
    cell_to_int = {}

    cells = list(tiling.point_cells.union(tiling.possibly_empty).union(tiling.positive_cells))
    for cell in cells:
        # TODO: use integer mapping
        cell_to_int[cell] = len(cell_to_int)

    components_set = UnionFind(len(cell_to_int))

    if non_interleaving_decomposition:
        for i in range(len(cells)):
            for j in range(i+1, len(cells)):
                c1 = cells[i]
                c2 = cells[j]
                if c1[0] == c2[0] or c1[1] == c2[1]:
                    components_set.unite(cell_to_int[c1], cell_to_int[c2])

    for ob in tiling:
        for i in range(len(ob.pos)):
            for j in range(i+1,len(ob.pos)):
                components_set.unite(cell_to_int[ob.pos[i]], cell_to_int[ob.pos[j]])

    all_components = {}
    for cell in cells:
        i = components_set.find(cell_to_int[cell])
        if i in all_components:
            all_components[i].append(cell)
        else:
            all_components[i] = [cell]
    cells_of_new_tilings = list(all_components.values())

    if len(cells_of_new_tilings) == 1:
        return
    strategy = []
    for new_cells in cells_of_new_tilings:
        point_cells = []
        possibly_empty = []
        positive_cells = []
        for cell in new_cells:
            if cell in tiling.possibly_empty:
                possibly_empty.append(cell)
            elif cell in tiling.point_cells:
                point_cells.append(cell)
            else:
                positive_cells.append(cell)
        obstructions = [ob for ob in tiling if ob.pos[0] in new_cells]

        strategy.append(Tiling(possibly_empty=possibly_empty,
                               positive_cells=positive_cells,
                               point_cells=point_cells,
                               obstructions=obstructions))

    yield Strategy("The components of the tiling",
                   strategy,
                   workable=[True for _ in strategy],
                   back_maps=[t.back_map for t in strategy])
# Consider the union of components?