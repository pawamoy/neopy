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


class QueryBuilder:
    def __init__(self):
        self.statements = QueryStatements()

    def add_match(self, *args, **kwargs):
        pass

    def add_where(self, *args, **kwargs):
        pass

    def add_create(self, *args, **kwargs):
        pass

    def add_delete(self, *args, **kwargs):
        pass

    def add_return(self, *args, **kwargs):
        pass

    def add_set(self, *args, **kwargs):
        pass

    def add_remove(self, *args, **kwargs):
        pass

    def add_merge(self, *args, **kwargs):
        pass
