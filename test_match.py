import orientdb as o




def main():
    odb = o.OrientDB("orient://root:password@cmshooter.homeip.net:2424/test")
    odb.open_db()

    m = o.Match()\
        .vertex("Word", "w")\
        .where("text=${text}", params={"text":"spirito"})\
        .out()\
        .vertex("Word", "s")\
        .result(["w.text", "s.text"])\
        .limit(5)

    print(m.compose())

    odb.close()
pass


if __name__ == "__main__":
    main()
