# neopy
Neo4j for Python. Manipulate graph data in Python with Neo4j as data storage.

The goal of this library is to provide a Python interface for querying and
manipulating data stored in a Neo4j database.

This is a very early attempt, not even alpha.

The first wanted feature is the ability to write Cypher queries in Python,
using the power of Cypher without its syntax. This results in a more verbose
but more flexible query language.

From Python to Cypher:

```python

from neopy import (
    Node as N, NodeLabel as L,
    Relationship as R,
    CypherQuerySet as Qs)


query = Qs().match(
    N('a'), R(), N(L('Movie'), name='The worst movie ever!')
).where(a__name__startswith='John').return_('a')

for record in query.run():
    print(record['name'])
```

Higher-level methods:

```python
from neopy import (
    Node as N, NodeLabel as L,
    RelationshipTo as Rt, RelationshipType as T)
    
   
node1 = N('id1', L('Label1'), hello='world!').create()
node2 = N('id2', L('Label2'), other_property='other_value').create()
node3 = N('id3', L('Label3'))

relationship1 = node1.connect(Rt(T('REL_TYPE1'), weight=9000), node2)

relationship2 = Rt('id4', T('REL_TYPE2'))
node1.connect(relationship2, node3)
```


