import topics_impl as t
import orientdb as o



def main():
    odb = o.OrientDB("orient://root:password@cmshooter.homeip.net:2424/test")
    odb.open_db()

    odb.create_class_vertex("Word", {"text": str})
    odb.create_class_edge("Synonimous")

    print(odb.list_classes())

    syn = t.Synonimous()
    syn.load_synonimous("topics/Italiano/th_it_IT_v2.txt")

    for w in syn:
        print(w)

        vw = odb.select_vertex("Word", where="text=${text}", params={"text": w})
        if vw is None:
            vw = odb.insert_vertex("Word", body={"text": w})

        slist = syn[w]
        for s in slist:
            print("... %s" % s)

    odb.close()


#end


if __name__ == "__main__":
    main()