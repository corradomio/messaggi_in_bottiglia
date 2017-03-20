import neo4jdb as n


def main(odb):
    print(odb.list_classes())
    print(odb.exists_class("Movie"))
    print(odb.exists_class("Moviex"))
    print(odb.list_properties("Movie"))
    print(odb.delete_node("Test"))
    print(odb.create_node("Test", {"t":1}))
    print(odb.create_node("Test", {"t":2}))
    print(odb.create_edge("REL", ("Test", {"t":1}), ("Test", {"t":2}) ))

    # print(odb.create_node("Actress", {"name": "Liv Tayles", "sexy": True}))
    # print(odb.delete_node("Actress", {"name": "Liv Tayles"}))
# end


if __name__ == "__main__":
    # odb = o.OrientDB("orient://root:password@cmshooter.homeip.net:2424/test")
    odb = n.Neo4jDB("bolt://neo4j:password@localhost:7687")
    odb.open_db()
    main(odb)
    odb.close()
