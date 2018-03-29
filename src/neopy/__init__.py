"""
Neo4j for Python.

Manipulate graph data in Python with Neo4j as data storage.
"""

__version__ = '0.1.0'

# driver = GraphDatabase.driver(uri, auth=("neo4j", "neo4j"))

# cypher language
# MATCH (nid1:label1) [rid:type] (nid2:label2)
# WHERE id1.property STARTS WITH "string"
# RETURN id1.property AS name1, collect(id2.property) as name2
# ORDER BY name1 ASC LIMIT x;

# [OPTIONAL] MATCH, WHERE, STARTS|ENDS WITH, RETURN, ORDER BY ... ASC|DESC,
# LIMIT, CREATE, FOREACH, AS, MERGE, IN, CONTAINS, DELETE, SET, REMOVE, MERGE

# collect, shortestPath, distinct, toInt, sum, count, avg, max

# >, <, >=, <=, =, =~

# Nodes:
# ()
# (id)
# (:label)
# (id:label)
# ({property:value})
# (:label1:label2) &&
# (:label1|label2) ||

# Relationships
# -->
# -[:type]->
# -[:type1|type2]->
# -[id]->
# -[id:type]->
# -[{property:value}]->
# -[:type*min..max]->

# Parameters cannot be used with
#   property keys; so, MATCH (n) WHERE n.$param = 'something' is invalid
#   relationship types
#   labels

# All reserved keywords:
# https://neo4j.com/docs/developer-manual/current/cypher/syntax/reserved/
