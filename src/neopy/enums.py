# -*- coding: utf-8 -*-

"""Enumerations module."""


class MetaEnum(type):
    ALL = ()

    def __contains__(cls, item):
        return item in cls.ALL
