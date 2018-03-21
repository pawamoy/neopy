"""NeoPy package."""

from collections import namedtuple, Iterable
from copy import deepcopy
import random
import string

from neo4j.v1 import GraphDatabase, types as neotypes

from .exceptions import CypherIdAlreadyUsed, CypherError

uri = "bolt://localhost:7687"
driver = GraphDatabase.driver(uri)
# driver = GraphDatabase.driver(uri, auth=("neo4j", "neo4j"))

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

# Parameters cannot be used with
#   property keys; so, MATCH (n) WHERE n.$param = 'something' is invalid
#   relationship types
#   labels

# All reserved keywords:
# https://neo4j.com/docs/developer-manual/current/cypher/syntax/reserved/


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


class LengthRange:
    def __init__(self, min_length, max_length):
        self.min = min_length
        self.max = max_length

    def as_cypher(self):
        return '*{min}..{max}'.format(min=self.min or '', max=self.max or '')


class ExactLength:
    def __init__(self, length):
        self.length = length

    def as_cypher(self):
        if self.length in (None, '*'):
            return '*'
        elif self.length == 1:
            return ''
        else:
            return '*%d' % self.length


class Properties(dict):
    def __getattr__(self, item):
        return self[item]

    def __setattr__(self, key, value):
        self[key] = value


class CypherQuerySet:
    def __init__(self):
        self.cypher = ''

        # We keep trace of the matched components so we only use
        # their cypher IDs in Create statements.
        self._matched_ids = set()

    def run(self):
        with driver.session() as session:
            with session.begin_transaction() as tx:
                return tx.run(self.cypher)

    @clone
    def match(self, *args, **kwargs):
        print('match query', args, kwargs)
        self.cypher += 'MATCH '
        for arg in args:
            self.cypher += arg.as_cypher()
        self.cypher += ' '
        return self

    def match_id(self, node, **kwargs):
        print('match id query', node, kwargs)
        if node.cypher_id:
            if node.cypher_id in self._matched_ids:
                raise CypherIdAlreadyUsed(node.cypher_id)
            node_cypher_id = node.cypher_id
        else:
            node_cypher_id = self.get_unused_id()
        self_clone = self.match(Node(node_cypher_id)).where(
            fn.Id(node_cypher_id).eq(node.internal_id))
        self_clone._matched_ids.add(node_cypher_id)
        self_clone.cypher += ' '
        return self_clone

    @clone
    def where(self, *conditions, **properties):
        print('where query', conditions, properties)
        self.cypher += 'WHERE '
        cypher_wheres = []
        if conditions:
            cypher_wheres.extend([c.as_cypher() for c in conditions])
        if properties:
            for p_key, p_value in properties.items():
                splits = p_key.split('__')
                if len(splits) == 1:
                    raise CypherError
                elif len(splits) == 2:
                    cypher_id, p_key = splits
                    if isinstance(p_value, Cypher):
                        p_value = p_value.as_cypher()
                    else:
                        p_value = cypher_primitive(p_value)
                    cypher_wheres.append('{}.{} = {}'.format(
                        cypher_id, p_key, p_value))
                elif len(splits) == 3:
                    cypher_id, p_key, operator = splits
                    pass  # TODO
                else:
                    raise CypherError
        self.cypher += ', '.join(cypher_wheres)
        return self

    @clone
    def create(self, *args, **kwargs):
        print('create query', args, kwargs)
        self.cypher += 'CREATE '
        for arg in args:
            if arg.cypher_id in self._matched_ids:
                self.cypher += arg.as_cypher(keys=['id'])
            else:
                self.cypher += arg.as_cypher()
        self.cypher += ' '
        return self

    @clone
    def return_(self, *args, **kwargs):
        print('return query', args, kwargs)
        self.cypher += 'RETURN '
        self.cypher += (', '.join(arg.cypher_id for arg in args)) + ' '
        return self

    @clone
    def delete(self, *args, **kwargs):
        print('delete query', args, kwargs)
        return self

    @clone
    def set(self, *args, **kwargs):
        print('set query', args, kwargs)
        return self

    @clone
    def remove(self, *args, **kwargs):
        print('remove query', args, kwargs)
        return self

    @clone
    def merge(self, *args, **kwargs):
        print('merge query', args, kwargs)
        return self

    def get_unused_id(self):
        letters = string.ascii_lowercase
        while True:
            new_id = ''.join(random.choice(letters) for _ in range(8))
            if new_id not in self._matched_ids:
                return new_id


class Cypher:
    cypher_template = ''

    def __str__(self):
        return self.as_cypher()

    def as_cypher(self, keys=None):
        params = self.cypher_params
        if keys:
            return self.cypher_template.format(**{
                k: v if k in keys else '' for k, v in params.items()})
        return self.cypher_template.format(**params)

    @property
    def cypher_params(self):
        raise NotImplementedError


class Function:
    class Id(Cypher):
        cypher_template = 'id({id})'

        def __init__(self, cypher_id):
            self.cypher_id = cypher_id

        @property
        def cypher_params(self):
            return dict(id=self.cypher_id)

        def eq(self, value):
            self.cypher_template += ' = {}'.format(value)
            return self


fn = Function()


class NodeLabel:
    def __init__(self, name):
        self.name = name


class Node(Cypher):
    cypher_template = '({id}{labels}{properties})'

    def __init__(self, *args, **properties):
        self.internal_id = None
        self.cypher_id, args = split_id_args(*args)
        self.labels = set(args)
        self.properties = Properties(**properties)

    @property
    def cypher_params(self):
        return {
            'id': self.cypher_id if self.cypher_id else '',
            'labels': ':' + ':'.join(l.name for l in self.labels) if self.labels else '',
            'properties': cypher_properties(self.properties)
        }

    def create(self, *args, **kwargs):
        print('create node', args, kwargs)
        records = list(CypherQuerySet().create(self).return_(self).run())
        created = records[0].value(self.cypher_id)
        self.internal_id = created.id
        return self

    def connect(self, relationship, node):
        # if node has internal id, pre-match it
        # query.match(self).create(self, rel, node).return_(rel)
        # return rel with start_node=self, end_node=node
        if not self.internal_id:
            raise CypherError
        query = CypherQuerySet().match_id(self)
        if relationship.cypher_id is None:
            relationship.cypher_id = query.get_unused_id()
        returns = [relationship]
        if node.internal_id is not None:
            query = query.match_id(node)
        else:
            returns.append(node)
        query = query.create(self, relationship, node).return_(*returns)
        for record in query.run():
            if isinstance(record, neotypes.Relationship):
                relationship.internal_id = record.id
                relationship.start_node = self
                relationship.end_node = node
            elif isinstance(record, neotypes.Node):
                node.internal_id = record.id
        return relationship

    def delete(self, *args, **kwargs):
        print('delete node', args, kwargs)
        return self

    def set(self, *args, **kwargs):
        print('set node', args, kwargs)
        return self

    def remove(self, *args, **kwargs):
        print('remove node', args, kwargs)
        return self

    def merge(self, *args, **kwargs):
        print('merge node', args, kwargs)
        return self


class RelationshipType:
    def __init__(self, name):
        self.name = name


class Relationship(Cypher):
    cypher_template = '-[{id}{types}{length}{properties}]-'

    def __init__(self, *args, **properties):
        self.internal_id = None
        self.cypher_id, args = split_id_args(*args)
        self.types = set(args)
        self.properties = Properties(**properties)
        self.length = ExactLength(1)

    def length(self, length):
        self.length = ExactLength(length)
        return self

    def range(self, min_length, max_length):
        self.length = LengthRange(min_length, max_length)
        return self

    @property
    def cypher_params(self):
        return {
            'id': self.cypher_id if self.cypher_id else '',
            'types': ':' + '|'.join(
                t.name for t in self.types) if self.types else '',
            'length': self.length.as_cypher(),
            'properties': cypher_properties(self.properties)
        }

    def delete(self, *args, **kwargs):
        print('delete relationship', args, kwargs)
        return self

    def set(self, *args, **kwargs):
        print('set relationship', args, kwargs)
        return self

    def remove(self, *args, **kwargs):
        print('remove relationship', args, kwargs)
        return self

    def merge(self, *args, **kwargs):
        print('merge relationship', args, kwargs)
        return self


class RelationshipTo(Relationship):
    cypher_template = '-[{id}{types}{length}{properties}]->'


class RelationshipFrom(Relationship):
    cypher_template = '<-[{id}{types}{length}{properties}]-'
