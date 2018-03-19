from collections import Iterable, namedtuple


def cypher_primitive(val):
    if isinstance(val, str):
        return '"%s"' % val
    elif val is None:
        return 'null'
    elif isinstance(val, Iterable):
        return '[%s]' % ','.join(cypher_primitive(v) for v in val)
    return str(val)


def cypher_escape(s):
    return '`%s`' % s


def cypher_properties(dct):
    if dct:
        return ' {' + ', '.join(
            '{k}: {v}'.format(k=k, v=cypher_primitive(v))
            for k, v in dct.items()) + '}'
    return ''


IdArgsTuple = namedtuple('id_args', 'id args')


def split_id_args(*args):
    if args:
        if isinstance(args[0], str):
            return IdArgsTuple(args[0], args[1:])
        return IdArgsTuple(None, args)
    return IdArgsTuple(None, [])


class Cypher:
    cypher_template = ''

    def __str__(self):
        return self.as_cypher()

    def as_cypher(self):
        print('rendering %s' % self.__class__)
        params = self.get_params()
        print(self.cypher_template)
        print(params)
        return self.cypher_template.format(params)

    def get_params(self):
        raise NotImplementedError


# ======================= COMPONENTS ==========================================
class Component(Cypher):
    def __init__(self, **properties):
        self.properties = properties or {}

    def set(self, **properties):
        self.properties.update(properties)


class Node(Component):
    cypher_template = '({id}{labels}{properties})'

    def __init__(self, *args, **properties):
        super(Node, self).__init__(**properties)
        self.id, args = split_id_args(*args)
        self.labels = set(args)

    def get_params(self):
        return {
            'id': self.id if self.id else '',
            'labels': ':'.join(l.name for l in self.labels),
            'properties': cypher_properties(self.properties)
        }


NodeLabel = namedtuple('NodeLabel', 'name')


class Relationship(Component):
    cypher_template = '-[{id}{types}{length}{properties}]-'

    def __init__(self, *args, **properties):
        super(Relationship, self).__init__(**properties)
        self.id, args = split_id_args(*args)
        self.types = set(args)
        self.exact_length = 1
        self.min_length = None
        self.max_length = None

    def min(self, min_length):
        self.min_length = min_length
        return self

    def max(self, max_length):
        self.max_length = max_length
        return self

    def length(self, length):
        self.exact_length = length
        return self

    def lengths(self, min_length, max_length):
        self.min_length = min_length
        self.max_length = max_length
        return self

    def get_length_param(self):
        if not (self.min_length is self.max_length is None):
            return '*{min}..{max}'.format(
                min=self.min_length if (self.min_length is not None) else '',
                max=self.max_length if (self.max_length is not None) else '')
        elif self.exact_length in (None, '*'):
            return '*'
        elif self.exact_length == 1:
            return ''
        else:
            return '*%d' % self.exact_length

    def get_params(self):
        return {
            'id': self.id if self.id else '',
            'types': ':' + '|'.join(t.name for t in self.types) if self.types else '',
            'length': self.get_length_param(),
            'properties': cypher_properties(self.properties)
        }


RelationshipType = namedtuple('RelationshipType', 'name')


class RelationshipTo(Relationship):
    cypher_template = '-[{id}{types}{length}{properties}]->'


class RelationshipFrom(Relationship):
    cypher_template = '<-[{id}{types}{length}{properties}]-'


class Path(Cypher):
    cypher_template = '{id}{components}'

    def __init__(self, *args):
        # TODO: assert number of components is odd
        # TODO: assert components are not Paths
        # TODO: assert components are Nodes and Relationships
        self.id, self.components = split_id_args(*args)

    def get_params(self):
        return {
            'id': (self.id + ' = ') if self.id else '',
            'components': ''.join(c.as_cypher() for c in self.components)
        }


class ShortestPath(Path):
    cypher_template = '{id}shortestpath( {components} )'


Identifier = namedtuple('Identifier', 'name')


# ======================= CLAUSES =============================================
class Clause(Cypher):
    pass


class Call(Clause):
    pass


class Create(Clause):
    cypher_template = 'CREATE {paths}'

    def __init__(self, *paths):
        self.paths = paths

    def get_params(self):
        return {'paths': ', '.join(p.as_cypher() for p in self.paths)}


class Delete(Clause):
    pass


class Detach(Clause):
    pass


class Exists(Clause):
    pass


class Foreach(Clause):
    pass


class Load(Clause):
    pass


class Match(Clause):
    cypher_template = 'MATCH {paths}'

    def __init__(self, *paths):
        self.paths = paths

    def get_params(self):
        return {'paths': ', '.join(p.as_cypher() for p in self.paths)}


class Merge(Clause):
    pass


class Optional(Clause):
    pass


class Remove(Clause):
    pass


class Return(Clause):
    pass


class Set(Clause):
    pass


class Start(Clause):
    pass


class Union(Clause):
    pass


class Unwind(Clause):
    pass


class With(Clause):
    pass


# ======================= SUBCLAUSES ==========================================
class Subclause(Clause):
    pass


class Limit(Subclause):
    pass


class Order(Subclause):
    pass


class Skip(Subclause):
    pass


class Where(Subclause):
    pass


class Yield(Subclause):
    pass


# ======================= MODIFIERS ===========================================
class Modifier(Cypher):
    def get_params(self):
        pass


class Asc(Modifier):
    pass


class Ascending(Modifier):
    pass


class Assert(Modifier):
    pass


class By(Modifier):
    pass


class Csv(Modifier):
    pass


class Desc(Modifier):
    pass


class Descending(Modifier):
    pass


class On(Modifier):
    pass


# ======================= EXPRESSIONS =========================================
class Expression(Cypher):
    def get_params(self):
        pass


class All(Expression):
    pass


class Case(Expression):
    pass


class Else(Expression):
    pass


class End(Expression):
    pass


class Then(Expression):
    pass


class When(Expression):
    pass


# ======================= OPERATORS ===========================================
class Operator(Cypher):
    def get_params(self):
        pass


class And(Operator):
    pass


class As(Operator):
    pass


class Contains(Operator):
    pass


class Distinct(Operator):
    pass


class Ends(Operator):
    pass


class In(Operator):
    pass


class Is(Operator):
    pass


class Not(Operator):
    pass


class Or(Operator):
    pass


class Starts(Operator):
    pass


class Xor(Operator):
    pass


# ======================= SCHEMA ==============================================
class Schema(Cypher):
    def get_params(self):
        pass


class Constraint(Schema):
    pass


# class Create(Schema):
#     pass


class Drop(Schema):
    pass


# class Exists(Schema):
#     pass


class Index(Schema):
    pass


# class Node(Schema):
#     pass


class Key(Schema):
    pass


class Unique(Schema):
    pass


# ======================= HINTS ===============================================
class Hint(Cypher):
    def get_params(self):
        pass


# class Index(Hint):
#     pass


class Join(Hint):
    pass


class Periodic(Hint):
    pass


class Commit(Hint):
    pass


class Scan(Hint):
    pass


class Using(Hint):
    pass


# ======================= LITERALS ============================================
class Literal(Cypher):
    def get_params(self):
        pass


# FIXME: use instances instead of classes?
class LiteralFalse(Literal):
    pass


class LiteralNull(Literal):
    pass


class LiteralTrue(Literal):
    pass


# ======================= RESERVED FOR FUTURE USE =============================
class FutureUse(Cypher):
    def get_params(self):
        pass


class Add(FutureUse):
    pass


class Do(FutureUse):
    pass


class For(FutureUse):
    pass


class Mandatory(FutureUse):
    pass


class Of(FutureUse):
    pass


class Require(FutureUse):
    pass


class Scalar(FutureUse):
    pass


# ======================= FUNCTIONS ===========================================
class Function(Cypher):
    def get_params(self):
        pass

    # https://neo4j.com/docs/developer-manual/current/cypher/functions/


class Predicate(Function):
    # all
    # any
    # exists
    # none
    # single
    pass


# class Scalar(Function):
    # coalesce
    # endNode
    # head
    # id
    # last
    # length
    # properties
    # size
    # startNode
    # timestamp
    # toBoolean
    # toFloat
    # toInteger
    # type
    # pass


class Aggregation(Function):
    # avg
    # collect
    # count
    # max
    # min
    # percentileCont
    # percentileDisc
    # stDev
    # stDevP
    # sum
    pass


class List(Function):
    # extract
    # filter
    # keys
    # labels
    # nodes
    # range
    # reduce
    # relationships
    # reverse
    # tail
    pass


class MathNumeric(Function):
    # abs
    # ceil
    # floor
    # rand
    # round
    # sign
    pass


class MathLogarithmic(Function):
    # e
    # exp
    # log
    # log10
    # sqrt
    pass


class MathTrigonometric(Function):
    # acos
    # asin
    # atan
    # atan2
    # cos
    # cot
    # degrees
    # haversin
    # pi
    # radians
    # sin
    # tan
    pass


class String(Function):
    # left
    # lTrim
    # replace
    # reverse
    # right
    # rTrim
    # split
    # substring
    # toLower
    # toString
    # toUpper
    # trim
    pass


class Spatial(Function):
    # distance
    # point
    pass
