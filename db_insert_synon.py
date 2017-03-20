import topics as t
import orientdb as o



def main():
    odb = o.OrientDB("orient://root:password@cmshooter.homeip.net:2424/test")
    odb.open_db()

    # odb.drop_class("VTest", unsafe=True)

    # odb.drop_class("Word")
    # odb.drop_class("Syn")
    #
    # odb.create_class("Word", body={"extends":"V", "text":str})
    # odb.create_index("Word.text", "UNIQUE")
    # odb.create_class("Syn", body={"extends":"E"})

    # odb.delete_vertex("Word")

    print(odb.list_classes())

    syn = t.Synonimous()
    syn.load_synonimous("topics/Italiano/th_it_IT_v2.txt")

    # for w in syn:
    #     vw = odb.insert_vertex("Word", body={"text": w})
    #     print(vw)

    for w in syn:
        print(w)

        vto = odb.get_document("Word", where="text=${text}", params={"text": w})
        vto = vto._rid

        slist = syn[w]
        for s in slist:
            vfrom = odb.get_document("Word", where="text=${text}", params={"text": s})
            vfrom = vfrom._rid

            print("... %s" % s)
            odb.insert_edge("Syn", vfrom, vto)
        # end

    odb.close()


#end


if __name__ == "__main__":
    main()