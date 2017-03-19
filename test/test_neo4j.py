from neo4jdb import *


def main():

    ndb = Neo4jDB("bolt://localhost:7687")
    ndb.connect("neo4j", "password")

    # print(Match("Person", "p").return_("p"))

    # ndb.create_node("Actor", {"name":"Corrado", "age":39, "extras": [1,2,3]})

    ret = ndb.match(Match("Person", "p").relation("ACTED_IN").match().return_("p"))
    print(ret)

pass



if __name__ == "__main__":
    main()