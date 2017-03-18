import orientdb

SERVER="orient://cmshooter.homeip.net:2424/testMG?u=admin&p=admin"


def main():

    print("=== OrientDB ===")

    # connect to the database
    odb = orientdb.OrientDB(SERVER)

    odb.open_db()

    odb.create_class("Question", body={"extends": "V", "topic": "string", "text": "string", "subject": "string", })
    odb.insert_vertex("Question", body={"topic": "ierbigb fbd", "text": "brbeb", "subject": "ehethetrq gre r "})

    # odb.drop_class("Vtest", unsafe=True)
    # odb.drop_class("Etest", unsafe=True)
    # odb.create_class("VTest", {"extends": "V", "name":str})
    # odb.create_class("ETest", {"extends": "E", "label":str, "weight":float})
    #
    # v1 = odb.create_vertex("VTest", body={"name": "pippo"})
    # v2 = odb.create_vertex("VTest", body={"name": "pluto"})
    # e1 = odb.create_edge("ETest", v1, v2, body={"label": "topolino"})
    # e1 = odb.update_edge(e1, body={"label": "topolino"})
    # print(v1)
    # print(v2)
    # print(e1)
    #
    # d = odb.get_document("VTest", v1)
    # print(d)
    #
    #


    odb.close_db()
# end


if __name__ == "__main__":
    main()
