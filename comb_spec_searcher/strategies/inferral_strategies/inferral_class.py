"""A wrapper for inferral strategies."""
from comb_spec_searcher.strategies import Strategy

def InferralStrategy(formal_step, obj):
    """A wrapper for inferral strategies."""
    return Strategy(formal_step, [obj], [True], [True], ignore_parent=True)
