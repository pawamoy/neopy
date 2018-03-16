from copy import deepcopy

from .enums import RelationshipDirection

# cypher language
# MATCH (nid1:label1) [rid:type] (nid2:label2)
# WHERE id1.property STARTS WITH "string"
# RETURN id1.property AS name1, collect(id2.property) as name2
# ORDER BY name1 ASC LIMIT x;

# [OPTIONAL] MATCH, WHERE, STARTS|ENDS WITH, RETURN, ORDER BY ... ASC|DESC, LIMIT, CREATE, FOREACH, AS, MERGE, IN, CONTAINS, DELETE, SET, REMOVE, MERGE
# collect, shortestPath, distinct, toInt, sum, count, avg, max
# >, <, >=, <=, =, =~

# Nodes:
# ()
# (id)
# (:label)
# (id:label)
# ({property:value})
# (:label1:label2) &&
# (:label1|label2) ||

# Relationships
# -->
# -[:type]->
# -[:type1|type2]->
# -[id]->
# -[id:type]->
# -[{property:value}]->
# -[:type*min..max]->


class CypherQuery:
    def __init__(self):
        pass

    def create(self, *args):
        pass

    def delete(self):
        pass

    # update for django
    def set(self):
        pass

    # no equivalent
    def remove(self):
        pass

    # get_or_create for django
    def merge(self):
        pass

    # get for django
    def match(self, *args, optional=False):
        pass

    # filter for django
    def where(self, **clauses):
        # .where(id__property=value)
        # .where(id__property__operator=value)
            # operator: gte, gt, lte, lt, startswith, endswith, contains
            #           istartwtih, iendswith, icontains, iexact, in
        pass

    # return for cypher
    def values(self):
        pass

    def order_by(self):
        pass

    def limit(self):
        pass

    # no equivalent
    def foreach(self):
        pass

    def rel(self):
        pass

    def rel_in(self):
        pass

    def rel_out(self):
        pass

    def node(self):
        pass


class Node:
    def __init__(self, *labels, **properties):
        self.variable_id = None
        if labels:
            if isinstance(labels[0], str):
                self.variable_id = labels[0]
                del labels[0]
        else:
            labels = []
        self.labels = set(labels)
        self.properties = properties

    def set(self, **properties):
        self_copy = deepcopy(self)
        self_copy.properties.update(properties)
        return self_copy


class NodeLabel:
    def __init__(self, value):
        self.value = value

    def __and__(self, other):
        self.value += ':' + other.value


class Relationship:
    Direction = RelationshipDirection

    def __init__(self, *types, **properties):
        self.variable_id = None
        if types:
            if isinstance(types[0], str):
                self.variable_id = types[0]
                del types[0]
        else:
            types = []
        self.types = types
        self.properties = properties
        self.direction = self.Direction.NONE
        self.min_value = None
        self.max_value = None

    def direct(self, direction):
        self_copy = deepcopy(self)
        self_copy.direction = direction
        return self_copy

    def min(self, value):
        self_copy = deepcopy(self)
        self_copy.min_value = value
        return self_copy

    def max(self, value):
        self_copy = deepcopy(self)
        self_copy.max_value = value
        return self_copy


class RelationshipType:
    def __init__(self, value):
        self.value = value

    def __or__(self, other):
        self.value += '|' + other.value


class RelationshipTo(Relationship):
    def __init__(self, *types, **properties):
        super().__init__(*types, **properties)
        self.direction = self.Direction.TO


class RelationshipFrom(Relationship):
    def __init__(self, *types, **properties):
        super().__init__(*types, **properties)
        self.direction = self.Direction.FROM


class ShortestPath:
    def __init__(self, *args):
        self.variable_id = None
        if args:
            if isinstance(args[0], str):
                self.variable_id = args[0]
                del args[0]
        else:
            args = []
        required = Node
        for arg in args:
            if not isinstance(arg, required):
                raise ValueError('Path input must be an interweaving '
                                 'of nodes and relationships')
            required = Relationship if required == Node else Node
        self.path_elements = args


class Variable:
    def __init__(self, name):
        self.name = name