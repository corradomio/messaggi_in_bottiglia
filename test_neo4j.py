import neo4jdb


def main():

    ndb = neo4jdb.Neo4jDB("bolt://localhost:7687")
    ndb.connect("neo4j", "password")

    ndb.create_node("Actor", {"name":"Corrado", "age":39, "extras": [1,2,3]})

pass



if __name__ == "__main__":
    main()