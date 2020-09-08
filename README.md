# neopy

[![ci](https://github.com/pawamoy/neopy/workflows/ci/badge.svg)](https://github.com/pawamoy/neopy/actions?query=workflow%3Aci)
[![documentation](https://img.shields.io/badge/docs-mkdocs%20material-blue.svg?style=flat)](https://pawamoy.github.io/neopy/)
[![pypi version](https://img.shields.io/pypi/v/neopy.svg)](https://pypi.org/project/neopy/)

Neo4j for Python. Manipulate graph data in Python with Neo4j as data storage.

The goal of this library is to provide a Python interface for querying and
manipulating data stored in a Neo4j database.

This is a very early attempt, not even alpha.

The first wanted feature is the ability to write Cypher queries in Python,
using the power of Cypher without its syntax. This results in a verbose
but composable query language.

From Python to Cypher:

```python
from neopy.graph import (
    Node as N, NodeLabel as L,
    RelationshipTo as Rt,
    RelationshipType as T,
    Graph)


you = N('you', L('Person'), name='You').create()

graph = Graph().match(you).create(
    you,
    Rt('like', T('like')),
    N('neo', L('Database'), name='Neo4j')
).return_(you, 'like', 'neo')

print(graph.query)

# MATCH (you:Person {name: "You"})
# CREATE (you)-[like:like]->(neo:Database {name: "Neo4j"})
# RETURN you, like, neo;
```

Just like in Django, the graph queries are lazy, so are only evaluated when
their results are accessed. There are no side-effects, as Graph methods
return a modified copy of the graph. It means you can compose queries without
modifying the previous ones:

```python
graph = Graph()

# prepare some query
match = graph.match(...)

# use the match object in different ways, and keep it unmodified
result1 = match.where(...).return_(...)
result2 = match.where(...).return_(...)

# run the same query as result2, but with an additional where condition
result3 = result2.where(...)
```

## Requirements

neopy requires Python 3.6 or above.

<details>
<summary>To install Python 3.6, I recommend using <a href="https://github.com/pyenv/pyenv"><code>pyenv</code></a>.</summary>

```bash
# install pyenv
git clone https://github.com/pyenv/pyenv ~/.pyenv

# setup pyenv (you should also put these three lines in .bashrc or similar)
export PATH="${HOME}/.pyenv/bin:${PATH}"
export PYENV_ROOT="${HOME}/.pyenv"
eval "$(pyenv init -)"

# install Python 3.6
pyenv install 3.6.8

# make it available globally
pyenv global system 3.6.8
```
</details>

## Installation

With `pip`:
```bash
python3.6 -m pip install neopy
```

With [`pipx`](https://github.com/pipxproject/pipx):
```bash
python3.6 -m pip install --user pipx

pipx install --python python3.6 neopy
```
