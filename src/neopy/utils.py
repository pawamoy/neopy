from collections import namedtuple
from copy import deepcopy


IdArgsTuple = namedtuple('id_args', 'id args')


def args_to_paths(*args):
    class Path: pass  # FIXME: temporary
    paths = []
    components = []
    for arg in args:
        if isinstance(arg, Path):
            if components:
                paths.append(Path(*components))
                components = []
            paths.append(arg)
        else:
            components.append(arg)
    if components:
        paths.append(Path(*components))
    return paths


def split_id_args(*args):
    if args:
        if isinstance(args[0], str):
            return IdArgsTuple(args[0], args[1:])
        return IdArgsTuple(None, args)
    return IdArgsTuple(None, [])


def clone(func):
    def new_func(obj, *args, **kwargs):
        obj = deepcopy(obj)
        return func(obj, *args, **kwargs)
    return new_func
