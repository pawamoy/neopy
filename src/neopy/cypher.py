from collections import Iterable


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
