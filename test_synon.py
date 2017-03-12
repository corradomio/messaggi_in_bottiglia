import topics_impl as t


syn = t.Synonimous()
syn.load_synonimous("topics/Italiano/th_it_IT_v2.txt")

for w in syn:
    print(w)
    slist = syn[w]
    for s in slist:
        print("... %s" % s)
