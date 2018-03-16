from copy import deepcopy

from neo4j.v1 import GraphDatabase

from .enums import RelationshipDirection, CypherStatementType

# driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "neo4j"))
driver = GraphDatabase.driver("bolt://localhost:7687")

# cypher language
# MATCH (nid1:label1) [rid:type] (nid2:label2)
# WHERE id1.property STARTS WITH "string"
# RETURN id1.property AS name1, collect(id2.property) as name2
# ORDER BY name1 ASC LIMIT x;

# [OPTIONAL] MATCH, WHERE, STARTS|ENDS WITH, RETURN, ORDER BY ... ASC|DESC,
# LIMIT, CREATE, FOREACH, AS, MERGE, IN, CONTAINS, DELETE, SET, REMOVE, MERGE

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


class CypherStatement:
    Types = CypherStatementType

    def __init__(self, statement, *args, **kwargs):
        if statement not in self.Types:
            raise ValueError('Unknown statement %s', statement)
        self.statement = statement
        self.args = args
        self.kwargs = kwargs

        self.string = ''
        self.params = {}

    def build(self):
        if self.statement == self.Types.CREATE:
            # list of node, rel, node, ...
            # simple node
            # path
            # list of paths
            if len(self.args) == 1:
                if isinstance(self.args[0], Node):
                    node = self.args[0]
                    self.string = 'CREATE ({id}{labels})'.format(
                        id=node.variable_id if node.variable_id else '',
                        labels=':' + ':'.join(node.labels) if node.labels else ''
                    )
                elif isinstance(self.args[0], Path):
                    pass

        elif self.statement == self.Types.DELETE:
            pass
        elif self.statement == self.Types.SET:
            pass
        elif self.statement == self.Types.REMOVE:
            pass
        elif self.statement == self.Types.MERGE:
            pass
        elif self.statement == self.Types.MATCH:
            pass
        elif self.statement == self.Types.WHERE:
            pass
        elif self.statement == self.Types.VALUES:
            pass
        elif self.statement == self.Types.ORDER_BY:
            pass
        elif self.statement == self.Types.LIMIT:
            pass
        elif self.statement == self.Types.FOREACH:
            pass


class CypherQuery:
    def __init__(self):
        self._statements = []
        self._built = False
        self._query_string = None
        self._query_params = None
        self._executed = False
        self._query_result = None

    def __str__(self):
        if not self._built:
            self._build()
        return self._query_string

    def _copy_add_statement(self, statement, *args, **kwargs):
        self_copy = deepcopy(self)
        self_copy._statements.append(
            CypherStatement(statement, *args, **kwargs))
        return self_copy

    def _build(self):
        query_string = ''
        query_params = {}
        for statement in self._statements:
            statement.build()
            query_string += statement.string
            query_params.update(statement.params)
        self._query_string = query_string
        self._built = True

    def _execute(self):
        def execute(tx, query, params):
            return tx.run(query, **params)
        with driver.session() as session:
            result = session.read_transaction(
                execute, self._query_string, self._query_params)
        self._query_result = result
        self._executed = True

    def create(self, *args, **kwargs):
        return self._copy_add_statement(
            CypherStatement.Types.CREATE, *args, **kwargs)

    def delete(self, *args, **kwargs):
        return self._copy_add_statement(
            CypherStatement.Types.DELETE, *args, **kwargs)

    # update for django
    def set(self, *args, **kwargs):
        return self._copy_add_statement(
            CypherStatement.Types.SET, *args, **kwargs)

    # no equivalent
    def remove(self, *args, **kwargs):
        return self._copy_add_statement(
            CypherStatement.Types.REMOVE, *args, **kwargs)

    # get_or_create for django
    def merge(self, *args, **kwargs):
        return self._copy_add_statement(
            CypherStatement.Types.MERGE, *args, **kwargs)

    # get for django
    def match(self, *args, optional=False, **kwargs):
        return self._copy_add_statement(
            CypherStatement.Types.MATCH, *args, optional=optional, **kwargs)

    # filter for django
    def where(self, *args, **kwargs):
        # .where(id__property=value)
        # .where(id__property__operator=value)
            # operator: gte, gt, lte, lt, startswith, endswith, contains
            #           istartwtih, iendswith, icontains, iexact, in
        return self._copy_add_statement(
            CypherStatement.Types.WHERE, *args, **kwargs)

    # return for cypher
    def values(self, *args, **kwargs):
        return self._copy_add_statement(
            CypherStatement.Types.VALUES, *args, **kwargs)

    def order_by(self, *args, **kwargs):
        return self._copy_add_statement(
            CypherStatement.Types.ORDER_BY, *args, **kwargs)

    def limit(self, *args, **kwargs):
        return self._copy_add_statement(
            CypherStatement.Types.LIMIT, *args, **kwargs)

    # no equivalent
    def foreach(self, *args, **kwargs):
        return self._copy_add_statement(
            CypherStatement.Types.FOREACH, *args, **kwargs)


class Node:
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
        if self.properties:
            properties = ' {' + ', '.join(
                '{k}: {v}'.format(k=k, v=repr(v)) for k, v in
                self.properties.items()) + '}'
        else:
            properties = ''
        return '({id}{labels}{properties})'.format(
            id=self.variable_id if self.variable_id else '',
            labels=''.join(l.to_ascii() for l in self.labels),
            properties=properties
        )


class NodeLabel:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return self.value

    def to_ascii(self):
        return ':' + self.value


class Relationship:
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
        if self.direction == self.Direction.NONE:
            rf = rt = '-'
        elif self.direction == self.Direction.FROM:
            rf = '<-'
            rt = '-'
        elif self.direction == self.Direction.TO:
            rf = '-'
            rt = '->'
        has_min = self.min_bound is not None
        has_max = self.max_bound is not None
        if not any((self.variable_id, self.types, has_min, has_max,
                    self.no_bounds, self.properties)):
            return '{rf}{rt}'.format(rf=rf, rt=rt)
        if self.no_bounds:
            length = '*'
        elif has_min and has_max:
            length = '*%d..%d' % (self.min_bound, self.max_bound)
        elif has_min:
            length = '*%d..' % self.min_bound
        elif has_max:
            length = '*..%d' % self.max_bound
        else:
            length = ''
        if self.properties:
            properties = ' {' + ', '.join(
                '{k}: {v}'.format(k=k, v=repr(v)) for k, v in
                self.properties.items()) + '}'
        else:
            properties = ''
        return '{rf}[{id}{types}{length}{properties}]{rt}'.format(
            rf=rf, rt=rt, id=self.variable_id if self.variable_id else '',
            types=':' + '|'.join(t.to_ascii() for t in self.types) if self.types else '',
            length=length, properties=properties
        )


class RelationshipType:
    def __init__(self, value):
        self.value = value

    def to_ascii(self):
        return self.value.upper()


class RelationshipTo(Relationship):
    def __init__(self, *types, **properties):
        super().__init__(*types, **properties)
        self.direction = self.Direction.TO


class RelationshipFrom(Relationship):
    def __init__(self, *types, **properties):
        super().__init__(*types, **properties)
        self.direction = self.Direction.FROM


class Path:
    def __init__(self, *args):
        if not args:
            raise ValueError('Path cannot be empty')
        required = Node
        for arg in args:
            if not isinstance(arg, required):
                raise ValueError('Path must be an interweaving '
                                 'of nodes and relationships')
            required = Relationship if required == Node else Node
        self.elements = args

    def to_ascii(self):
        return ''.join(e.to_ascii() for e in self.elements)


class ShortestPath(Path):
    def __init__(self, *args):
        self.variable_id = None
        if args:
            if isinstance(args[0], str):
                self.variable_id = args[0]
                args = args[1:]
        super().__init__(*args)


class Variable:
    def __init__(self, name):
        self.name = name