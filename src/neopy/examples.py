from unittest import TestCase

from .graph import (
    Node as N, Relationship as Rel, RelationshipTo as RelTo,
    NodeLabel as L, RelationshipType as T, CypherQuery as Q)


class Person(N):
    def __init__(self, *labels, **properties):
        super().__init__(*labels, **properties)
        self.labels.add(L('Person'))


def get_result(query):
    records = query.run()
    records_list = list(records)
    first_record = records_list[0]
    first_record_values = first_record.values()
    return first_record_values
    # return list(query.run())[0].values()


def example1():
    # CREATE (you:Person {name:"You"})
    # RETURN you
    query = Q().create(N('you', L('Person'), name='You')).return_('you')

    # The following should could also work, implicitly:
    # query = Q().create(N('you', L('Person'), name='You'))

    return get_result(query)


def example2():
    # MATCH  (you:Person {name:"You"})
    # CREATE (you)-[like:LIKE]->(neo:Database {name:"Neo4j" })
    # RETURN you,like,neo
    person_label = L('Person')
    you = N('you', person_label, name='You')
    like = RelTo('like', T('like'))
    neo = N('neo', L('Database'), name='Neo4j')
    query = Q()\
        .match(you)\
        .create(you, like, neo)\
        .return_(you, like, neo)

    return get_result(query)


def example3_naive_python():
    # MATCH (you:Person {name:"You"})
    # FOREACH (name in ["Johan","Rajesh","Anna","Julia","Andrew"] |
    #   CREATE (you)-[:FRIEND]->(:Person {name:name}))

    you = Person('you', name='You')
    names = ["Johan", "Rajesh", "Anna", "Julia", "Andrew"]
    friend = RelTo(T('friend'))

    queries = []

    # naive solution with Python for-loop
    for name in names:
        queries.append(
            Q().match(you).create(you, friend, Person(name=name)).return_(you))

    return [get_result(q) for q in queries]


def example3_naive_concat():
    # MATCH (you:Person {name:"You"})
    # FOREACH (name in ["Johan","Rajesh","Anna","Julia","Andrew"] |
    #   CREATE (you)-[:FRIEND]->(:Person {name:name}))

    you = Person('you', name='You')
    names = ["Johan", "Rajesh", "Anna", "Julia", "Andrew"]
    friend = RelTo(T('friend'))

    # naive solution with query concatenation
    query = Q()
    for i, name in enumerate(names):
        cid = 'id%s' % i
        query = query.create(you, friend, Person(cid, name=name)).return_(cid)
    return get_result(query)


def example3_foreach():
    # MATCH (you:Person {name:"You"})
    # FOREACH (name in ["Johan","Rajesh","Anna","Julia","Andrew"] |
    #   CREATE (you)-[:FRIEND]->(:Person {name:name}))

    you = Person('you', name='You')
    names = ["Johan", "Rajesh", "Anna", "Julia", "Andrew"]
    friend = RelTo(T('friend'))

    # solution with built-in Neo4j foreach method
    name_variable = I('name')
    query = Q().match(you).foreach(
        name_variable, names, Q().create(
            you, friend, Person(name=name_variable)
        )
    )
    return get_result(query)


def example4():
    # MATCH (you {name:"You"})-[:FRIEND]->(yourFriends)
    # RETURN you, yourFriends
    query = Q().match(
        N('you', name='You'),
        RelTo(T('friend')),
        N('yourFriends')
    ).return_('you', 'yourFriends')
    return get_result(query)


def example5():
    # MATCH (neo:Database {name:"Neo4j"})
    # MATCH (anna:Person {name:"Anna"})
    # CREATE (anna)-[:FRIEND]->(:Person:Expert {name:"Amanda"})-[:WORKED_WITH]->(neo)
    person = L('Person')
    neo = N('neo', L('Database'), name='Neo4j')
    anna = N('anna', person, name='Anna')

    query = Q().match(neo).match(anna).create(
        anna, RelTo(T('friend')),
        N(person, name='Amanda'),
        RelTo(T('worked_with')), neo)
    return get_result(query)


def example6_flat():
    # MATCH (you {name:"You"})
    # MATCH (expert)-[:WORKED_WITH]->(db:Database {name:"Neo4j"})
    # MATCH path = shortestPath( (you)-[:FRIEND*..5]-(expert) )
    # RETURN db,expert,path

    query = Q()\
        .match(N('you', name='You'))\
        .match(N('expert'), RelTo(T('worked_with')), N('db', L('Database'), name='Neo4j'))\
        .match(Sp('path', N('you'), Rel(T('friend')).range(None, 5), N('expert')))\
        .return_('db', 'expert', 'path')

    return get_result(query)


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
    path = Sp('path', you, friend.range(None, 5), expert)

    query = Q()\
        .match(you.set(name='You'))\
        .match(expert, worked_with, db)\
        .match(path)\
        .return_(db, expert, path)

    return get_result(query)


def example7():
    # OPTIONAL MATCH (user:User)-[FRIENDS_WITH]-(friend:User)
    # WHERE user.Id = 1234
    # RETURN user, count(friend) AS NumberOfFriends

    def Count(v): return v

    query = Q().optional_match(
        N('user', L('User')),
        Rel(T('friends_with')),
        N('friend', L('User'))
    ).where(user__id=1234).return_('user', number_of_friends=Count('friend'))

    user_label = L('User')
    user = N('user', user_label)
    friend = N('friend', user_label)
    rel = Rel(T('friends_with'))
    n_of_f = Count(friend)

    query = Q().optional_match(
        user, rel, friend).where(user__id=1234).return_(user, n_of_f)

    return get_result(query)


class MainTestCase(TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_example1(self):
        result = example1()
        print(result)

    def test_example2(self):
        result = example2()
        print(result)

    def test_example3(self):
        result1 = example3_naive_python()
        print(result1)
        result2 = example3_naive_concat()
        print(result2)
        # result3 = example3_foreach()
        # print(result3)

    def test_example4(self):
        result = example4()
        print(result)

    def test_example5(self):
        result = example5()
        print(result)

    def test_example6(self):
        result1 = example6_composed()
        print(result1)
        result2 = example6_flat()
        print(result2)

    def test_example7(self):
        result = example7()
        print(result)

