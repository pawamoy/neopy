from neo4j.v1 import types

from .cypher import Cypher, Properties, Query
from .db import driver
from .exceptions import CypherIdAlreadyUsed, CypherError
from .functions import fn
from .utils import split_id_args, clone


class Graph:
    def __init__(self):
        self.query = Query()

    def run(self):
        with driver.session() as session:
            with session.begin_transaction() as tx:
                return tx.run(self.query.render())

    @clone
    def match(self, *args, **kwargs):
        self.query.add_match(*args, **kwargs)
        return self

    def match_id(self, node):
        if node.cypher_id:
            if node.cypher_id in self.query.matched_ids:
                raise CypherIdAlreadyUsed(node.cypher_id)
            node_cypher_id = node.cypher_id
        else:
            node_cypher_id = self.query.get_unused_id()
        self_clone = self.match(Node(node_cypher_id)).where(
            fn.Id(node_cypher_id).eq(node.internal_id))
        self_clone.query.matched_ids.add(node_cypher_id)
        return self_clone

    @clone
    def where(self, *conditions, **properties):
        self.query.add_where(*conditions, **properties)
        return self

    @clone
    def create(self, *args, **kwargs):
        self.query.add_create(*args, **kwargs)
        return self

    @clone
    def return_(self, *args, **kwargs):
        self.query.add_return(*args, **kwargs)
        return self

    @clone
    def delete(self, *args, **kwargs):
        self.query.add_delete(*args, **kwargs)
        return self

    @clone
    def set(self, *args, **kwargs):
        self.query.add_set(*args, **kwargs)
        return self

    @clone
    def remove(self, *args, **kwargs):
        self.query.add_remove(*args, **kwargs)
        return self

    @clone
    def merge(self, *args, **kwargs):
        self.query.add_merge(*args, **kwargs)
        return self


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
            'properties': self.properties.as_cypher()
        }

    def create(self):
        records = list(Graph().create(self).return_(self).run())
        created = records[0].value(self.cypher_id)
        self.internal_id = created.id
        return self

    def connect(self, relationship, node):
        if not self.internal_id:
            raise CypherError
        graph = Graph().match_id(self)
        if relationship.cypher_id is None:
            relationship.cypher_id = graph.query.get_unused_id()
        returns = [relationship]
        if node.internal_id is not None:
            graph = graph.match_id(node)
        else:
            returns.append(node)
        graph = graph.create(self, relationship, node).return_(*returns)
        for record in graph.run():
            if isinstance(record, types.Relationship):
                relationship.internal_id = record.id
                relationship.start_node = self
                relationship.end_node = node
            elif isinstance(record, types.Node):
                node.internal_id = record.id
        return relationship

    def delete(self, *args, **kwargs):
        print('delete node', *(str(a) for a in args), kwargs)
        return self

    def set(self, *args, **kwargs):
        print('set node', *(str(a) for a in args), kwargs)
        return self

    def remove(self, *args, **kwargs):
        print('remove node', *(str(a) for a in args), kwargs)
        return self

    def merge(self, *args, **kwargs):
        print('merge node', *(str(a) for a in args), kwargs)
        return self


class RelationshipType:
    def __init__(self, name):
        self.name = name


class Relationship(Cypher):
    cypher_template = '-[{id}{types}{length}{properties}]-'

    class LengthRange:
        def __init__(self, min_length, max_length):
            self.min = min_length
            self.max = max_length

        def as_cypher(self):
            return '*{min}..{max}'.format(min=self.min or '',
                                          max=self.max or '')

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

    def __init__(self, *args, **properties):
        self.internal_id = None
        self.cypher_id, args = split_id_args(*args)
        self.types = set(args)
        self.properties = Properties(**properties)
        self.length = Relationship.ExactLength(1)

    def length(self, length):
        self.length = Relationship.ExactLength(length)
        return self

    def range(self, min_length, max_length):
        self.length = Relationship.LengthRange(min_length, max_length)
        return self

    @property
    def cypher_params(self):
        return {
            'id': self.cypher_id if self.cypher_id else '',
            'types': ':' + '|'.join(
                t.name for t in self.types) if self.types else '',
            'length': self.length.as_cypher(),
            'properties': self.properties.as_cypher()
        }

    def delete(self, *args, **kwargs):
        print('delete relationship', *(str(a) for a in args), kwargs)
        return self

    def set(self, *args, **kwargs):
        print('set relationship', *(str(a) for a in args), kwargs)
        return self

    def remove(self, *args, **kwargs):
        print('remove relationship', *(str(a) for a in args), kwargs)
        return self

    def merge(self, *args, **kwargs):
        print('merge relationship', *(str(a) for a in args), kwargs)
        return self


class RelationshipTo(Relationship):
    cypher_template = '-[{id}{types}{length}{properties}]->'


class RelationshipFrom(Relationship):
    cypher_template = '<-[{id}{types}{length}{properties}]-'
