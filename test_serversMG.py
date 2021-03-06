
SERVER="192.168.1.66"
# SERVER="192.168.1.10"

# ---------------------------------------------------------------------------
# Neo4j
# ---------------------------------------------------------------------------
# pip install neo4j-driver
#
# http://192.168.244.143:7474/browser/
#
#   neo4j / password|admin
#

from neo4j.v1 import GraphDatabase, basic_auth

print("=== Neo4j ===")

# basic_auth("neo4j", "neo4j")
driver = GraphDatabase.driver("bolt://%s:7687" % SERVER, auth=basic_auth("neo4j", "centos"))
session = driver.session()
print(session)


# ---------------------------------------------------------------------------
# OrientDB
# ---------------------------------------------------------------------------
# pip install pyorient
#
# http://192.168.244.143:2480
#
#   admin / admin
#   root / root
#

import pyorient

print("=== OrientDB ===")

client = pyorient.OrientDB(SERVER, 2424)
session = client.connect("root", "root")
print(session)


# ---------------------------------------------------------------------------
# MongoDB
# ---------------------------------------------------------------------------
# pip install pymongo
#

import pymongo

print("=== MongoDB ===")

client = pymongo.MongoClient(SERVER, 27017)
dbs = client. database_names()
print(dbs)
client.close()


# ---------------------------------------------------------------------------
# MySQL
# ---------------------------------------------------------------------------
# pip3 install mysql-connector
#
#
# import mysql.connector
#
# print("=== MySQL ===")
#
# cnx = mysql.connector.connect(host=SERVER, database='mysql',
#                               user='root', password='password')
# print(cnx)
# cnx.close()
#

# ---------------------------------------------------------------------------
# ArangoDB
# ---------------------------------------------------------------------------
# pip3 install pyarango
#
# import pyArango.connection as acon
#
# print("=== ArangoDB ===")
#
# conn = acon.Connection(arangoURL="http://{0}:8529".format(SERVER), username="root", password="")
# print(conn.databases)
