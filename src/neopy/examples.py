from neo4j.v1 import GraphDatabase

from . import (
    Node as N, Relationship as Rel, RelationshipTo as RelTo,
    RelationshipFrom as RelFrom, NodeLabel as L, RelationshipType as T,
    ShortestPath as P, CypherQuery, Variable as V)


# driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))


def example1():
    # CREATE (you:Person {name:"You"})
    # RETURN you
    query = CypherQuery().create(N('you', L('Person'), name='You')).values('you')

    # The following should could also work, implicitly:
    # query = CypherQuery().create(N('you', L('Person'), name='You'))

    return query


def example2():
    # MATCH  (you:Person {name:"You"})
    # CREATE (you)-[like:LIKE]->(neo:Database {name:"Neo4j" })
    # RETURN you,like,neo
    person_label = L('Person')
    you = N('you', person_label, name='You')
    like = RelTo('like', T('like'))
    neo = N('neo', L('Database'), name='Neo4j')
    query = CypherQuery()\
        .match(you)\
        .create(you, like, neo)\
        .values(you, like, neo)

    return query


def example3():
    # MATCH (you:Person {name:"You"})
    # FOREACH (name in ["Johan","Rajesh","Anna","Julia","Andrew"] |
    #   CREATE (you)-[:FRIEND]->(:Person {name:name}))
    person_label = L('Person')

    class Person(N):
        def __init__(self, *labels, **properties):
            super().__init__(*labels, **properties)
            self.labels.add(person_label)

    you = Person('you', name='You')
    names = ["Johan", "Rajesh", "Anna", "Julia", "Andrew"]
    friend = RelTo(T('friend'))

    queries = {}

    # naive solution with Python for-loop
    for name in names:
        query = CypherQuery().create(you, friend, Person(name=name))
        queries['naive python'] = query

    # naive solution with query concatenation
    query = CypherQuery()
    for name in names:
        query = query.create(you, friend, Person(name=name))
    queries['naive concat'] = query

    # solution with built-in Neo4j foreach method
    name_variable = V('name')
    query = CypherQuery().match(you).foreach(
        name_variable, names, CypherQuery().create(
            you, friend, Person(name=name_variable)
        )
    )
    queries['foreach'] = query

    return queries


def example4():
    # MATCH (you {name:"You"})-[:FRIEND]->(yourFriends)
    # RETURN you, yourFriends
    query = CypherQuery().match(
        N('you', name='You'),
        RelTo(T('friend')),
        N('yourFriends')
    ).values('you', 'yourFriends')
    return query


def example5():
    # MATCH (neo:Database {name:"Neo4j"})
    # MATCH (anna:Person {name:"Anna"})
    # CREATE (anna)-[:FRIEND]->(:Person:Expert {name:"Amanda"})-[:WORKED_WITH]->(neo)
    person = L('Person')
    neo = N('neo', L('Database'), name='Neo4j')
    anna = N('anna', person, name='Anna')

    query = CypherQuery().match(neo).match(anna).create(
        anna, RelTo(T('friend')),
        N(person, name='Amanda'),
        RelTo(T('worked_with')), neo)
    return query


def example6_flat():
    # MATCH (you {name:"You"})
    # MATCH (expert)-[:WORKED_WITH]->(db:Database {name:"Neo4j"})
    # MATCH path = shortestPath( (you)-[:FRIEND*..5]-(expert) )
    # RETURN db,expert,path

    query = CypherQuery()\
        .match(N('you', name='You'))\
        .match(N('expert'), RelTo(T('worked_with')), N('db', L('Database'), name='Neo4j'))\
        .match(P('path', N('you'), Rel(T('friend')).max(5), N('expert')))\
        .values('db', 'expert', 'path')

    return query


def example6_composed():
    # MATCH (you {name:"You"})
    # MATCH (expert)-[:WORKED_WITH]->(db:Database {name:"Neo4j"})
    # MATCH path = shortestPath( (you)-[:FRIEND*..5]-(expert) )
    # RETURN db,expert,path
    you = N('you')
    expert = N('expert')
    db = N('db', L('Database'), name='Neo4j')
    worked_with = RelTo(T('worked_with'))
    friend = Rel(T('friend'))
    path = P('path', you, friend.max(5), expert)

    query = CypherQuery()\
        .match(you.set(name='You'))\
        .match(expert, worked_with, db)\
        .match(path)\
        .values(db, expert, path)

    return query


def official():
    def add_friends(tx, name, friend_name):
        tx.run("MERGE (a:Person {name: $name}) "
               "MERGE (a)-[:KNOWS]->(friend:Person {name: $friend_name})",
               name=name, friend_name=friend_name)

    def print_friends(tx, name):
        for record in tx.run(
                "MATCH (a:Person)-[:KNOWS]->(friend) WHERE a.name = $name "
                "RETURN friend.name ORDER BY friend.name", name=name):
            print(record["friend.name"])

    with driver.session() as session:
        session.write_transaction(add_friends, "Arthur", "Guinevere")
        session.write_transaction(add_friends, "Arthur", "Lancelot")
        session.write_transaction(add_friends, "Arthur", "Merlin")
        session.read_transaction(print_friends, "Arthur")