class CypherQuery:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

        self.string = ''
        self.params = {}

    def build(self):
        pass

