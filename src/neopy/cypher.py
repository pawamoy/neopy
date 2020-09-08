import copy
import random
import string
from collections import Iterable, namedtuple

from .exceptions import CypherError

StatementArgs = namedtuple("StatementArgs", "args kwargs")


def cypher_primitive(val):
    if isinstance(val, str):
        return '"%s"' % val
    elif val is None:
        return "null"
    elif isinstance(val, Iterable):
        return "[%s]" % ",".join(cypher_primitive(v) for v in val)
    return str(val)


def cypher_escape(s):
    return "`%s`" % s


class Properties(dict):
    def __getattr__(self, item):
        return self[item]

    def __setattr__(self, key, value):
        self[key] = value

    def __deepcopy__(self, memo):
        return Properties(copy.deepcopy(dict(self)))

    def as_cypher(self):
        if not self:
            return ""
        return " {" + ", ".join("{k}: {v}".format(k=k, v=cypher_primitive(v)) for k, v in self.items()) + "}"


class Cypher:
    cypher_template = ""

    def __str__(self):
        return self.as_cypher()

    def as_cypher(self, keys=None):
        params = self.cypher_params
        if keys:
            return self.cypher_template.format(**{k: v if k in keys else "" for k, v in params.items()})
        return self.cypher_template.format(**params)

    @property
    def cypher_params(self):
        raise NotImplementedError


class QueryStatements:
    def __init__(self):
        self.matches = []
        self.wheres = []
        self.creates = []
        self.deletes = []
        self.returns = []
        self.sets = []
        self.removes = []
        self.merges = []


class Query:
    def __init__(self):
        self.statements = QueryStatements()

        # We keep trace of the matched components so we use
        # their cypher IDs only in Create statements.
        self.matched_ids = set()

        # We keep trace of the created components so we use
        # their cypher IDs only in further statements.
        self.created_ids = set()

    def __str__(self):
        return self.render()

    def add_match(self, *args, **kwargs):
        self.statements.matches.append(StatementArgs(args, kwargs))

    def add_where(self, *args, **kwargs):
        self.statements.wheres.append(StatementArgs(args, kwargs))

    def add_create(self, *args, **kwargs):
        self.statements.creates.append(StatementArgs(args, kwargs))

    def add_delete(self, *args, **kwargs):
        self.statements.deletes.append(StatementArgs(args, kwargs))

    def add_return(self, *args, **kwargs):
        self.statements.returns.append(StatementArgs(args, kwargs))

    def add_set(self, *args, **kwargs):
        self.statements.sets.append(StatementArgs(args, kwargs))

    def add_remove(self, *args, **kwargs):
        self.statements.removes.append(StatementArgs(args, kwargs))

    def add_merge(self, *args, **kwargs):
        self.statements.merges.append(StatementArgs(args, kwargs))

    def render(self):
        statements = []

        if self.statements.matches:
            statements.append(self.render_matches())
        if self.statements.wheres:
            statements.append(self.render_wheres())
        if self.statements.creates:
            statements.append(self.render_creates())
        if self.statements.deletes:
            statements.append(self.render_deletes())
        if self.statements.returns:
            statements.append(self.render_returns())
        if self.statements.sets:
            statements.append(self.render_sets())
        if self.statements.removes:
            statements.append(self.render_removes())
        if self.statements.merges:
            statements.append(self.render_merges())

        return " ".join(statements) + ";"

    def render_matches(self):
        cyphers = []
        for match in self.statements.matches:
            cypher_matches = []
            for arg in match.args:
                cypher_matches.append(arg.as_cypher())
                if hasattr(arg, "cypher_id") and arg.cypher_id:
                    self.matched_ids.add(arg.cypher_id)
            cyphers.append("MATCH " + "".join(cypher_matches))
        return " ".join(cyphers)

    def render_wheres(self):
        cyphers = []
        for where in self.statements.wheres:
            cypher_wheres = []
            if where.args:
                cypher_wheres.extend([a.as_cypher() for a in where.args])
            if where.kwargs:
                for p_key, p_value in where.kwargs.items():
                    splits = p_key.split("__")
                    if len(splits) == 1:
                        raise CypherError
                    elif len(splits) == 2:
                        cypher_id, p_key = splits
                        if isinstance(p_value, Cypher):
                            p_value = p_value.as_cypher()
                        else:
                            p_value = cypher_primitive(p_value)
                        cypher_wheres.append("{}.{} = {}".format(cypher_id, p_key, p_value))
                    elif len(splits) == 3:
                        cypher_id, p_key, operator = splits
                        pass  # TODO
                    else:
                        raise CypherError
            cyphers.append("WHERE " + ", ".join(cypher_wheres))
        return " ".join(cyphers)

    def render_creates(self):
        cyphers = []
        for create in self.statements.creates:
            cypher_creates = []
            for arg in create.args:
                if hasattr(arg, "cypher_id") and arg.cypher_id:
                    if arg.cypher_id in self.matched_ids | self.created_ids:
                        cypher_creates.append(arg.as_cypher(keys=["id"]))
                    else:
                        cypher_creates.append(arg.as_cypher())
                        self.created_ids.add(arg.cypher_id)
                else:
                    cypher_creates.append(arg.as_cypher())
            cyphers.append("CREATE " + "".join(cypher_creates))
        return " ".join(cyphers)

    def render_deletes(self):
        pass

    def render_returns(self):
        cyphers = []
        for return_ in self.statements.returns:
            cypher_returns = []
            for arg in return_.args:
                if isinstance(arg, Cypher) and hasattr(arg, "cypher_id"):
                    cypher_returns.append(arg.cypher_id)
                elif isinstance(arg, str):
                    cypher_returns.append(arg)
            cyphers.append("RETURN " + ", ".join(cypher_returns))
        return " ".join(cyphers)

    def render_sets(self):
        pass

    def render_removes(self):
        pass

    def render_merges(self):
        pass

    def get_unused_id(self):
        letters = string.ascii_lowercase
        while True:
            new_id = "".join(random.choice(letters) for _ in range(8))
            if new_id not in self.matched_ids:
                return new_id
