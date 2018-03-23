from .cypher import Cypher


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
