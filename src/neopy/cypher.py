from collections import Iterable, namedtuple


StatementArgs = namedtuple('StatementArgs', 'args kwargs')


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


class Properties(dict):
    def __getattr__(self, item):
        return self[item]

    def __setattr__(self, key, value):
        self[key] = value

    def as_cypher(self):
        if not self:
            return ''
        return ' {' + ', '.join(
            '{k}: {v}'.format(k=k, v=cypher_primitive(v))
            for k, v in self.items()) + '}'


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
        self._matched_ids = set()

        # We keep trace of the created components so we use
        # their cypher IDs only in further statements.
        self._created_ids = set()

    def add_match(self, *args, **kwargs):
        self.statements.matches.append(StatementArgs(args, kwargs))

    def add_where(self, *args, **kwargs):
        self.statements.matches.append(StatementArgs(args, kwargs))

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

        return ' '.join(statements) + ';'

    def render_matches(self):
        cyphers = []
        for match in self.statements.matches:
            cypher = 'MATCH '
            for arg in match.args:
                cypher += arg.as_cypher()
                if hasattr(arg, 'cypher_id') and arg.cypher_id:
                    self._matched_ids.add(arg.cypher_id)
            cyphers.append(cypher)
        return ' '.join(cyphers)

    def render_wheres(self):
        pass

    def render_creates(self):
        pass

    def render_deletes(self):
        pass

    def render_returns(self):
        pass

    def render_sets(self):
        pass

    def render_removes(self):
        pass

    def render_merges(self):
        pass
