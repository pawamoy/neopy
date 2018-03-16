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
