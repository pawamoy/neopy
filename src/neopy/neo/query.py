from collections import namedtuple
from copy import deepcopy

from .db import driver
from .enums import RelationshipDirection

from .cypher import Create, Path, Match


def args_to_paths(*args):
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


class CypherQuerySet:
    def __init__(self):
        self.statements = []
        self._built = False
        self._executed = False
        self._query_result = None

    def __str__(self):
        return ''.join(s.as_cypher() for s in self.statements)

    def _clone(self):
        return deepcopy(self)

    def create(self, *args, **kwargs):
        clone = self._clone()
        paths = args_to_paths(*args)
        clone.statements.append(Create(*paths))
        return clone

    def delete(self, *args, **kwargs):
        clone = self._clone()
        clone.statements.append(*args, **kwargs)
        return clone

    # update for django
    def set(self, *args, **kwargs):
        clone = self._clone()
        clone.statements.append(*args, **kwargs)
        return clone

    # no equivalent
    def remove(self, *args, **kwargs):
        clone = self._clone()
        clone.statements.append(*args, **kwargs)
        return clone

    # get_or_create for django
    def merge(self, *args, **kwargs):
        clone = self._clone()
        clone.statements.append(*args, **kwargs)
        return clone

    # get for django
    def match(self, *args, optional=False, **kwargs):
        clone = self._clone()
        paths = args_to_paths(*args)
        clone.statements.append(Match(*paths))
        return clone

    # filter for django
    def where(self, *args, **kwargs):
        # .where(id__property=value)
        # .where(id__property__operator=value)
            # operator: gte, gt, lte, lt, startswith, endswith, contains
            #           istartwtih, iendswith, icontains, iexact, in
        clone = self._clone()
        clone.statements.append(*args, **kwargs)
        return clone

    # return for cypher
    def values(self, *args, **kwargs):
        clone = self._clone()
        clone.statements.append(*args, **kwargs)
        return clone

    def order_by(self, *args, **kwargs):
        clone = self._clone()
        clone.statements.append(*args, **kwargs)
        return clone

    def limit(self, *args, **kwargs):
        clone = self._clone()
        clone.statements.append(*args, **kwargs)
        return clone

    # no equivalent
    def foreach(self, *args, **kwargs):
        clone = self._clone()
        clone.statements.append(*args, **kwargs)
        return clone


class CypherNode:
    def __init__(self, *labels, **properties):
        self.variable_id = None
        if labels:
            if isinstance(labels[0], str):
                self.variable_id = labels[0]
                labels = labels[1:]
        else:
            labels = []
        self.labels = set(labels)
        self.properties = properties

    def set(self, **properties):
        self_copy = deepcopy(self)
        self_copy.properties.update(properties)
        return self_copy

    def to_ascii(self):
        return '({id}{labels}{properties})'.format(
            id=self.to_ascii_id(),
            labels=self.to_ascii_labels(),
            properties=self.to_ascii_properties()
        )

    def to_ascii_id(self):
        return self.variable_id if self.variable_id else ''

    def to_ascii_labels(self):
        return ''.join(l.to_ascii() for l in self.labels)

    def to_ascii_properties(self):
        if self.properties:
            properties = ' {' + ', '.join(
                '{k}: {v}'.format(k=k, v=repr(v)) for k, v in
                self.properties.items()) + '}'
        else:
            properties = ''
        return properties


class CypherNodeLabel:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return self.value

    def to_ascii(self):
        return ':' + self.value


class CypherRelationship:
    Direction = RelationshipDirection

    def __init__(self, *types, **properties):
        self.variable_id = None
        if types:
            if isinstance(types[0], str):
                self.variable_id = types[0]
                types = types[1:]
        else:
            types = []
        self.types = set(types)
        self.properties = properties
        self.direction = self.Direction.NONE
        self.min_bound = None
        self.max_bound = None
        self.no_bounds = False

    def __bool__(self):
        return any((self.variable_id, self.types, self.has_min, self.has_max,
                    self.no_bounds, self.properties))

    @property
    def has_min(self):
        return self.min_bound is not None

    @property
    def has_max(self):
        return self.max_bound is not None

    def direct(self, direction):
        self_copy = deepcopy(self)
        self_copy.direction = direction
        return self_copy

    def bound(self, min_bound=None, max_bound=None):
        self_copy = deepcopy(self)
        if min_bound is None and max_bound is None:
            self_copy.no_bounds = True
        else:
            if min_bound is not None:
                if min_bound < 0:
                    raise ValueError('min length boundary cannot be negative')
                self_copy.min_bound = min_bound
            if max_bound is not None:
                if max_bound < 0:
                    raise ValueError('max length boundary cannot be negative')
                elif min_bound is not None and max_bound < min_bound:
                    raise ValueError('max length boundary cannot be less than '
                                     'min length boundary')
                self_copy.max_bound = max_bound
        return self_copy

    def to_ascii(self):
        rel_left, rel_right = self.to_ascii_direction()
        if not bool(self):
            return '{rl}{rr}'.format(rl=rel_left, rr=rel_right)
        return '{rl}[{id}{types}{length}{properties}]{rr}'.format(
            rl=rel_left, rr=rel_right,
            id=self.to_ascii_id(),
            types=self.to_ascii_types(),
            length=self.to_ascii_length(),
            properties=self.to_ascii_properties()
        )

    def to_ascii_id(self):
        return self.variable_id if self.variable_id else ''

    def to_ascii_types(self):
        return ':' + '|'.join(t.to_ascii() for t in self.types) if self.types else ''

    def to_ascii_properties(self):
        if self.properties:
            properties = ' {' + ', '.join(
                '{k}: {v}'.format(k=k, v=repr(v)) for k, v in
                self.properties.items()) + '}'
        else:
            properties = ''
        return properties

    def to_ascii_direction(self):
        if self.direction == self.Direction.FROM:
            rf, rt = '<-', '-'
        elif self.direction == self.Direction.TO:
            rf, rt = '-', '->'
        else:
            rf = rt = '-'
        return namedtuple('direction', 'rel_left rel_right')(rf, rt)

    def to_ascii_length(self):
        if self.no_bounds:
            length = '*'
        elif self.has_min and self.has_max:
            length = '*%d..%d' % (self.min_bound, self.max_bound)
        elif self.has_min:
            length = '*%d..' % self.min_bound
        elif self.has_max:
            length = '*..%d' % self.max_bound
        else:
            length = ''
        return length


class CypherRelationshipType:
    def __init__(self, value):
        self.value = value

    def to_ascii(self):
        return self.value.upper()


class CypherRelationshipTo(CypherRelationship):
    def __init__(self, *types, **properties):
        super().__init__(*types, **properties)
        self.direction = self.Direction.TO


class CypherRelationshipFrom(CypherRelationship):
    def __init__(self, *types, **properties):
        super().__init__(*types, **properties)
        self.direction = self.Direction.FROM


class CypherPath:
    def __init__(self, *args):
        if not args:
            raise ValueError('Path cannot be empty')
        required = CypherNode
        for arg in args:
            if not isinstance(arg, required):
                raise ValueError('Path must be an interweaving '
                                 'of nodes and relationships')
            required = CypherRelationship if required == CypherNode else CypherNode
        self.elements = args

    def to_ascii(self):
        return ''.join(e.to_ascii() for e in self.elements)


class CypherShortestPath(CypherPath):
    def __init__(self, *args):
        self.variable_id = None
        if args:
            if isinstance(args[0], str):
                self.variable_id = args[0]
                args = args[1:]
        super().__init__(*args)


class CypherVariable:
    def __init__(self, name):
        self.name = name

    def to_ascii(self):
        return self.name


# Q = CypherQuery
Qs = CypherQuerySet
N = CypherNode
L = CypherNodeLabel
R = CypherRelationship
Rt = CypherRelationshipTo
Rf = CypherRelationshipFrom
P = CypherPath
Sp = CypherShortestPath
V = CypherVariable
