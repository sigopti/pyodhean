"""Various utils"""


def pluck(parameters, key):
    """Return a dict with only a single given value per key

    Example: ::
        d = {
            'k1': {'a': 1, 'b':2},
            'k2': {'a': 3, 'b':4},
        }
        pluck(d, 'a')
        # {'k1': 1, 'k2': 3}
        pluck(d, 'b')
        # {'k1': 2, 'k2': 4}
    """
    return {k: v[key] for k, v in parameters.items()}
