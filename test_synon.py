import topics_impl as t
import orientdb as o



def main():
    syn = t.Synonimous()
    syn.load_synonimous("topics/Italiano/th_it_IT_v2.txt")

    odb = o.OrientDB

    for w in syn:
        print(w)
        slist = syn[w]
        for s in slist:
            print("... %s" % s)
#end


if __name__ == "__main__":
    main()