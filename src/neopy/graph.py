import random
import string

from neo4j.v1 import types

from .cypher import Cypher, Properties, cypher_primitive
from .db import driver
from .exceptions import CypherIdAlreadyUsed, CypherError
from .functions import fn
from .query import QueryBuilder
from .utils import split_id_args, clone


# TODO: amaybe rename CypherQuery "Graph"
# from neopy.graph import Graph
# graph = Graph()
# results = graph.match()...
# for r in results: ...

class CypherQuery:
    def __init__(self):
        self.cypher = ''  # TODO: remove when QueryBuilder is ready
        self.query = QueryBuilder()

        # TODO: move this in QueryBuilder
        # We keep trace of the matched components so we use
        # their cypher IDs only in Create statements.
        self._matched_ids = set()

        # TODO: move this in QueryBuilder
        # We keep trace of the created components so we use
        # their cypher IDs only in further statements.
        self._created_ids = set()

    def run(self):
        print('run query ', self.cypher)
        with driver.session() as session:
            with session.begin_transaction() as tx:
                return tx.run(self.cypher)

    @clone
    def match(self, *args, **kwargs):
        print('match query', *(str(a) for a in args), kwargs)
        self.cypher += 'MATCH '
        for arg in args:
            self.cypher += arg.as_cypher()
            if hasattr(arg, 'cypher_id'):
                self._matched_ids.add(arg.cypher_id)
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
        print('create query', *(str(a) for a in args), kwargs)
        self.cypher += 'CREATE '
        for arg in args:
            if hasattr(arg, 'cypher_id') and arg.cypher_id:
                if arg.cypher_id in self._matched_ids | self._created_ids:
                    self.cypher += arg.as_cypher(keys=['id'])
                else:
                    self.cypher += arg.as_cypher()
                    self._created_ids.add(arg.cypher_id)
            else:
                self.cypher += arg.as_cypher()
        self.cypher += ' '
        return self

    @clone
    def return_(self, *args, **kwargs):
        print('return query', *(str(a) for a in args), kwargs)
        self.cypher += 'RETURN '
        cypher_ids = []
        for arg in args:
            if isinstance(arg, Cypher) and hasattr(arg, 'cypher_id'):
                cypher_ids.append(arg.cypher_id)
            elif isinstance(arg, str):
                cypher_ids.append(arg)
        self.cypher += ', '.join(cypher_ids) + ' '
        return self

    @clone
    def delete(self, *args, **kwargs):
        print('delete query', *(str(a) for a in args), kwargs)
        return self

    @clone
    def set(self, *args, **kwargs):
        print('set query', *(str(a) for a in args), kwargs)
        return self

    @clone
    def remove(self, *args, **kwargs):
        print('remove query', *(str(a) for a in args), kwargs)
        return self

    @clone
    def merge(self, *args, **kwargs):
        print('merge query', *(str(a) for a in args), kwargs)
        return self

    def get_unused_id(self):
        letters = string.ascii_lowercase
        while True:
            new_id = ''.join(random.choice(letters) for _ in range(8))
            if new_id not in self._matched_ids:
                return new_id


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

    def create(self, *args, **kwargs):
        print('create node', *(str(a) for a in args), kwargs)
        records = list(CypherQuery().create(self).return_(self).run())
        created = records[0].value(self.cypher_id)
        self.internal_id = created.id
        return self

    def connect(self, relationship, node):
        # if node has internal id, pre-match it
        # query.match(self).create(self, rel, node).return_(rel)
        # return rel with start_node=self, end_node=node
        if not self.internal_id:
            raise CypherError
        query = CypherQuery().match_id(self)
        if relationship.cypher_id is None:
            relationship.cypher_id = query.get_unused_id()
        returns = [relationship]
        if node.internal_id is not None:
            query = query.match_id(node)
        else:
            returns.append(node)
        query = query.create(self, relationship, node).return_(*returns)
        for record in query.run():
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
