# -*- coding: utf-8 -*-

"""Enumerations module."""


class MetaEnum(type):
    ALL = ()

    def __contains__(cls, item):
        return item in cls.ALL


class RelationshipDirection(metaclass=MetaEnum):
    NONE = 0
    TO = 1
    FROM = -1

    ALL = (TO, FROM, NONE)


class CypherStatementType(metaclass=MetaEnum):
    CREATE = 0
    DELETE = 1
    SET = 2
    REMOVE = 3
    MERGE = 4
    MATCH = 5
    WHERE = 6
    VALUES = 7
    ORDER_BY = 8
    LIMIT = 9
    FOREACH = 10

    ALL = (CREATE, DELETE, SET, REMOVE, MERGE, MATCH, WHERE, VALUES, ORDER_BY,
           LIMIT, FOREACH)
