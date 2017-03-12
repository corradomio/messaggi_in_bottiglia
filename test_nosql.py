
# SERVER="192.168.244.143"
SERVER="192.168.1.3"

# from urllib.parse import urlparse
#
# o = urlparse('orientdb://192.168.1.3:2424?u=root,p=password')
# print(o[0]) # schema
# print(o[1]) # netloc
# print(o[2]) # path
# print(o[3]) # params
# print(o[4]) # query
# print(o[5]) # fragment

# ---------------------------------------------------------------------------
# OrientDB
# ---------------------------------------------------------------------------
# pip install pyorient
#
# http://192.168.244.143:2480
#
#   admin / admin
#   root / password | root
#
# http://192.168.1.3:2480
#   root / password | root
#

import orientdb


print("=== OrientDB ===")

# client = pyorient.OrientDB(SERVER, 2424)
# session_id = client.connect("root", "password")
# print(session_id)
# print(client.db_list())

# msgsinbttle
# GratefulDeadConcerts

# db_name="msgsinbttle"
# if not client.db_exists(db_name):
#     client.db_create(db_name, pyorient.DB_TYPE_GRAPH, pyorient.STORAGE_TYPE_PLOCAL)



# odb = orientdb.OrangeDB('orientdb://192.168.1.3:2424/GratefulDeadConcerts?u=root,p=password')
odb = orientdb.OrangeDB('orientdb://192.168.1.3:2424?u=root,p=password')
odb.connect()
print(odb.list_databases())
# odb.drop_db("test")
# odb.drop_db("other")
# odb.create_db("test",  db_type="graph",  drop_if_exists=True)

odb.open_db("test", db_type="graph")

# odb.drop_class("Vtest", unsafe=True)
# odb.drop_class("Etest", unsafe=True)
# odb.create_class("VTest", {"extends": "V", "name":str})
# odb.create_class("ETest", {"extends": "E", "label":str, "weight":float})

v1 = odb.create_vertex("VTest", body={"name": "pippo"})
v2 = odb.create_vertex("VTest", body={"name": "pluto"})
e1 = odb.create_edge("ETest", v1, v2, body={"label": "topolino"})
e1 = odb.update_edge(e1, body={"label": "topolino"})
print(v1)
print(v2)
print(e1)

d = odb.get_document("VTest", v1)
print(d)

odb.close_db()

# odb.connect()
# odb.drop_db("test")

# odb.open_db("msgsinbttle")
#
# odb = orientdb.OrangeDB('orientdb://192.168.1.3:2424/msgsinbttle?u=root,p=password')
# odb.connect()

# print(odb.list_databases())
# print(odb.list_classes())
# print(odb.exists_class("Student"))
# print(odb.list_properties("Student"))
# if odb.exists_class("Test"):
#     odb.drop_class("Test")
#
# print(odb.create_class("Test", {
#     "str": str,
#     "int": int,
#     "float": float,
#     "list": list,
#     "dict": dict,
#     "set": set}))
# print(odb.create_property("Test.str", str))
# print(odb.create_property("Test.int", int))
# print(odb.create_property("Test.float", float))
# print(odb.create_property("Test.list", list))
# print(odb.create_property("Test.dict", dict))
# print(odb.create_property("Test.set", set))

# print(odb.exists_class("Test"))
# print(odb.list_properties("Test"))
#
# v1 = odb.create_vertex("Test")
# v2 = odb.create_vertex("Test")
#
# print(v1)
# print(v2)


# print(odb.drop_class("Test"))
# print(odb.exists_class("Test"))

# if not odb.exists_class("Word"):
#     odb.create_class("Word")

odb.close()



