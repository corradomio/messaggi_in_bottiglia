import urlx
import pyorient
import json


# ===========================================================================
# Utilities
# ===========================================================================

def strof(v):
    return json.dumps(v)


# BOOLEAN
# SHORT INTEGER LONG
# FLOAT DOUBLE
# DATE
# STRING BINARY
# BYTE
#
# LINK
# EMBEDDED
#
# LINKLIST  EMBEDDEDLIST
# LINKSET   EMBEDDEDSET
# LINKMAP   EMBEDDEDMAP
#

otypes = {
    str: "STRING",
    float: "DOUBLE",
    int: "INTEGER",
    set: "LINKSET",
    dict: "LINKMAP",
    list: "LINKLIST"
}

def otype(stype):
    if stype in otypes:
        return otypes[stype]
    else:
        return stype


def odata(orec):
    if type(orec) == list:
        return [o._OrientRecord__o_storage for o in orec]
    else:
        return orec._OrientRecord__o_storage


def orid(orec):
    if type(orec) == list:
        return [o._OrientRecord__rid for o in orec]
    else:
        return orec._OrientRecord__rid


def vbodyof(body, op="SET"):
    """
    :param dict body:
    :return str:
    """
    if body is None or len(body) == 0:
        return ""
    set = ""
    for name in body:
        if len(set) == 0:
            set = op + " "
        else:
            set += ","
        set += ("%s = %s" % (name, strof(body[name])))
    return set


def jbodyof(body, op="CONTENT"):
    """
    :param dict body:
    :return str:
    """
    if body is None:
        return ""
    if len(body) == 0:
        return ""
    else:
        return "%s %s" % (op, json.dumps(body))

def vof(v):
    """
    :param str|list v:
    :return:
    """
    if v is None:
        return None
    if type(v) == list:
        return "[%s]" % str.join(",", v)
    if v.startswith("#"):
        return v
    else:
        return "(%s)" % v

# ===========================================================================
# OrientDB
# ===========================================================================
#
# Simple wrapper on 'pyorient.client' to simplify the major operations
#
# There are 2 group of operations:
#
# 1) create a connection to the server AND list the defined databases,
#    create a new database, destroy a database, etc
# 2) create a connection to the server AND select a specific database,
#    create classes, insert, update delete instances, navigate the graph
#
# The values for the command are more flexible dictionaries
#

class OrangeDB:

    # =======================================================================
    #
    # =======================================================================

    def __init__(self, url):
        """
        :param str url: "orientdb://host:port/db?u=user&p=password
        """
        assert url.startswith("orientdb:")

        self._url = urlx.parse(url)
        self._client = None
        self._session = None
        self._db = None

        host = self._url["host"]
        port = self._url.get("port", 2424)

        self._client = pyorient.OrientDB(host, port)
    # end

    # =======================================================================
    #   connect
    #       list_databases
    #       create_db
    #       exists_db
    #       drop_db
    #   close
    # =======================================================================

    def connect(self, user=None, password=None):
        """
        Connect to a OrientDB but doesn't open any database

        :param str user:
        :param str password:
        :return: session id
        """
        if user is None:
            user = self._url["username"]
            password = self._url["password"]

        self._session = self._client.connect(user, password)
        return self._session
    # end

    def close(self):
        pass
    # end

    # -----------------------------------------------------------------------
    # database
    # -----------------------------------------------------------------------
    # create/drop
    # insert/delete
    #

    def list_databases(self, full=False):
        """
        List of defined databases

        :param bool full: if to return all informations
        :return list[str] | dict:
        """
        databases = odata(self._client.db_list())
        """:type: dict"""
        databases = databases["databases"]
        if not full:
            return list(databases.keys())
        else:
            return databases
    # end

    def exists_db(self, db_name, storage_type=None):
        """
        Check if a database exists


        Note: WHY is necessary to specify the storage_type ???

        :param str db_name:
        :param str storage_type:
        :return bool:
        """
        if storage_type is None:
            storage_type = pyorient.STORAGE_TYPE_PLOCAL
        ret = self._client.db_exists(db_name, storage_type)
        return ret
    # end

    def create_db(self, db_name, db_type=None, storage_type=None, drop_if_exists=False):
        """
        Create a new database. Drop the current if necessary

        :param str db_name:
        :param str db_type: 'graph' or 'document'
        :param storage_type: 'plocal' or 'memory'
        :param bool drop_if_exists:
        :return bool:
        """
        if db_type is None:
            db_type = pyorient.DB_TYPE_GRAPH
        if storage_type is None:
            storage_type = pyorient.STORAGE_TYPE_PLOCAL
        if drop_if_exists and self._client.db_exists(db_name, storage_type):
            ret = self._client.db_drop(db_name)
        if not self._client.db_exists(db_name, storage_type):
            ret = self._client.db_create(db_name, db_type, storage_type)
            return True
        else:
            return False
    # end

    def drop_db(self, db_name):
        """
        Drop a database

        :param str db_name:
        :return:
        """
        try:
            ret = self._client.db_drop(db_name)
            return ret
        except pyorient.exceptions.PyOrientCommandException:
            return None
    # end

    # =======================================================================
    # open_db
    #   ...
    # close_db
    # =======================================================================

    def open_db(self, db_name=None, db_type=None, user=None, password=None):
        """
        Connect to a OrientDB server and open a database.

        If a parameter is not specified, it is retrieved from the url

        :param str db_name:
        :param str db_type:
        :param str user:
        :param str password:
        :return:
        """
        if db_name is None:
            db_name = self._url["path"][1:]
            db_type = self._url["db_type"]

        if user is None:
            user = self._url["username"]
            password = self._url["password"]

        if db_type is None:
            db_type = pyorient.DB_TYPE_GRAPH

        self._db = self._client.db_open(db_name,
            user=user, password=password, db_type=db_type)
    # end

    def close_db(self):
        """
        Close the current opened database

        :return:
        """
        if not self._db:
            return False

        self._client.db_close(self._db)
        self._db = None
        return True
    # end


    # -----------------------------------------------------------------------
    # class & property
    # -----------------------------------------------------------------------

    def list_classes(self, full=False):
        """
        List the classes defined in the database

        :param bool full: if to return all information
        :return list[str|dict:
        """
        command = "SELECT expand(classes) FROM metadata:schema"
        classes = self._client.command(command)
        classes = odata(classes)
        if not full:
            classes = [c["name"] for c in classes]
        return classes
    # end

    def list_properties(self, class_name, full=False):
        """
        List the properties of a class

        :param str class_name:
        :param bool full: if to return all information
        :return list[str]|dict:
        """
        command = "SELECT expand(properties) FROM (SELECT expand(classes) FROM metadata:schema) WHERE name = '%s'" % \
                  class_name
        cprops = self._client.command(command)
        cprops = odata(cprops)
        if not full:
            cprops = [p["name"] for p in cprops]
        return cprops
    # end

    def exists_class(self, class_name):
        """
        Check if a class exists

        :param str class_name:
        :return bool:
        """
        command = "SELECT * FROM (SELECT expand(classes) FROM metadata:schema) WHERE name = '%s'" % \
                  class_name
        aclass = self._client.command(command)
        return len(aclass) > 0
    # end

    def create_class(self, class_name, props, drop_if_exists=False):
        """
        Create a class
        Add the properties specified in 'props.

        Some property names are reserved:

        - 'extends':  to specify that the class extends a super_class
        - 'abstract': to specify that the class is abstract

            props["extends"]: str   = super_class
            props["abstract"]: bool = False

        for the other properties, the value is the type of the property.
        It is possible to use the OrientDB type or the Python type

            prop["name"]:type = str
            prop["name"]:str  = "STRING"


        :param str class_name:
        :param dict props: field definitions
        :return list:
        """
        if self.exists_class(class_name):
            if not drop_if_exists:
                return False
            else:
                self.drop_class(class_name)

        extends = props.get("extends", None)
        """:type: str"""
        abstract = props.get("abstract", False)
        """:type: str"""

        ret = []
        if class_name:
            command = ("CREATE CLASS %s %s %s" % (
                class_name,
                ("" if not extends  else "EXTENDS " + extends),
                ("" if not abstract else "ABSTRACT"))).strip()
            ret.extend(self._client.command(command)) # [id]

        for name in props:
            if name in ["extends", "abstract"]:
                continue
            pname = "%s.%s" % (class_name, name)
            ptype = otype(props[name])
            command = ("CREATE PROPERTY %s %s" % (pname, ptype))
            ret.extend(self._client.command(command))  # [id]

        return ret
    # end

    def drop_class(self, class_name, unsafe=False):
        """
        Drop a class

        :param str class_name:
        :param bool unsafe:
        :return:
        """
        command = ("DROP CLASS %s %s" % (
            class_name,
            ("" if not unsafe else "UNSAFE"))).strip()
        ret = self._client.command(command)  # [True]
        return ret
    # end

    def create_property(self, property, type, link=None, unsafe=False):
        """
        Create a property.

        The property must be a form:

            <class_name>.<property_name>

        The type can be a OrientDB type or a Python type

        :param str property:
        :param str|type type:
        :param str link:
        :param bool unsafe:
        :return:
        """
        command = ("CREATE PROPERTY %s %s %s %s" % (
            property,
            otype(type),
            ("" if link is None else link),
            ("" if not unsafe else "UNSAFE"))).strip()
        ret = self._client.command(command)
        return ret
    # end

    def drop_property(self, property, force=False):
        """
        Drop a property

        :param str property:
        :param bool force:
        :return:
        """
        command = ("DROP PROPERTY %s %s" % (
            property,
            ("" if not force else "FORCE"))).strip()
        ret = self._client.command(command)
        return ret
    # end

    # -----------------------------------------------------------------------
    # vertex & edge
    # -----------------------------------------------------------------------

    def create_vertex(self, class_name, body=None):
        """
        Create a vertex (a instance of the specified class), and set the
        body with 'body'

        Note: the class MUST extends 'V'

        :param str class_name:
        :param dict body:
        :return str: rid
        """
        jbody = jbodyof(body)
        command = ("CREATE VERTEX %s %s" % (class_name, jbody)).strip()
        ret = self._client.command(command)
        return orid(ret)[0]
    # end

    def delete_vertex(self, rid, where=None, limit=None):
        """
        Delete a vertex

        :param str rid: (rid) vertex identifier
        :param str where:
        :param int limit:
        :return:
        """
        command = ("DELETE VERTEX %s %s %s" % (
            rid,
            ("" if not where else "WHERE " + where),
            ("" if not limit else "LIMIT " + str(limit)))).strip()
        ret = self._client.command(command)
        return ret
    # end

    def update_vertex(self, rid, body=None, merge=None,
                        set=None, add=None, put=None, remove=None, incr=None,
                        where=None, limit=None):
        return self.update_document(rid,
                                    body=body,
                                    merge=merge,
                                    set=set,
                                    add=add,
                                    put=put,
                                    remove=remove,
                                    incr=incr,
                                    where=where,
                                    limit=limit)
    # end


    def create_edge(self, class_name, vfrom, vto, body=None):
        """
        Create a edge between two vertices, and set the
        body with 'body'

        Note: the class MUST extends 'E'

        :param str class_name:
        :param str vfrom: (rid)
        :param str vto:  (rid)
        :param dict body:
        :return str: rid
        """

        vfrom = vof(vfrom)
        vto = vof(vto)

        command = ("CREATE EDGE %s FROM %s TO %s" % (
            class_name,
            vfrom,
            vto)).strip()
        ret = self._client.command(command)
        rid = orid(ret[0])

        #
        # A quanto sempbra, NON FUNZIONA creare un edge e impostare direttamente
        # il body. Soluzione: 2 passi
        #
        if body is not None:
            command = ("UPDATE EDGE %s %s" % (rid, jbodyof(body)))
            ret = self._client.command(command)

        return rid
    # end

    def delete_edge(self, vfrom, vto=None, where=None, limit=None):
        """

        Note: vfram can be a class_name, a rid (starts with "#") or a list of
        rids.

        :param str|list vfrom: (rid) or list[(rid)] or class_name
        :param str vto: (rid)
        :param str where:
        :param int limit:
        :return:
        """

        vlist = vof(vfrom)
        if vto is not None:
            vlist = "FROM %s TO %s" % (vlist, vof(vto))

        command = ("DELETE EDGE %s %s %s" % (
            ("" if not vlist else vlist),
            ("" if not where else "WHERE " + where),
            ("" if not limit else "LIMIT " + str(limit)))).strip()
        ret = self._client.command(command)
        return ret
    # end

    def update_edge(self, rid, body=None, merge=None,
                        set=None, add=None, put=None, remove=None, incr=None,
                        where=None, limit=None):
        """
        Update the specified document

        :param str rid: rid or class_name
        :param dict body: replace the current body
        :param dict merge: merge with the current body
        :param dict set: Defines the fields to update.
        :param dict add: Adds a new item in collection fields.
        :param dict put: Puts an entry into a map field.
        :param dict remove: Removes an item in collection and map fields.
        :param dict incr: Increments the field by the value.
        :param where:
        :param limit:
        :return:
        """

        command = ("UPDATE EDGE %s %s %s %s %s %s %s %s %s %s" % (
            rid,
            ("" if set is None else vbodyof(set, "SET")),
            ("" if incr is None else vbodyof(set, "INCREMENT")),
            ("" if add is None else vbodyof(set, "ADD")),
            ("" if remove is None else vbodyof(set, "REMOVE")),
            ("" if put is None else vbodyof(set, "PUT")),
            ("" if body is None else jbodyof(body, "CONTENT")),
            ("" if merge is None else jbodyof(merge, "MERGE")),
            ("" if where is None else "WHERE " + where),
            ("" if limit is None else "LIMIT " + str(limit)))).strip()
        ret = self._client.command(command)
        return ret
    # end

    # -----------------------------------------------------------------------
    # create document
    # -----------------------------------------------------------------------
    #
    # 'body' | 'merge' must be a object convertible in JSON format
    #

    def insert_document(self, class_name, body):
        jbody = jbodyof(body)
        command = ("INSERT INTO CLASS:%s %s RETURN @rid" % (
                        class_name,
                        jbody)).strip()
        ret = self._client.command(command)
        return ret
    # end

    def update_document(self, rid, body=None, merge=None,
                        set=None, add=None, put=None, remove=None, incr=None,
                        where=None, limit=None):
        """
        Update the specified document

        :param str rid: rid or class_name
        :param dict body: replace the current body
        :param dict merge: merge with the current body
        :param dict set: Defines the fields to update.
        :param dict add: Adds a new item in collection fields.
        :param dict put: Puts an entry into a map field.
        :param dict remove: Removes an item in collection and map fields.
        :param dict incr: Increments the field by the value.
        :param where:
        :param limit:
        :return:
        """
        command = ("UPDATE %s %s %s %s %s %s %s %s %s %s" % (
            rid,
            ("" if set is None else vbodyof(set, "SET")),
            ("" if incr is None else vbodyof(set, "INCREMENT")),
            ("" if add is None else vbodyof(set, "ADD")),
            ("" if remove is None else vbodyof(set, "REMOVE")),
            ("" if put is None else vbodyof(set, "PUT")),
            ("" if body is None else jbodyof(body, "CONTENT")),
            ("" if merge is None else jbodyof(merge, "MERGE")),
            ("" if where is None else "WHERE " + where),
            ("" if limit is None else "LIMIT " + str(limit)))).strip()
        ret = self._client.command(command)
        return ret
    # end

    def delete_documents(self, class_name, where=None, limit=None):
        """

        :param str class_name:
        :param str where:
        :param int limit:
        :return:
        """
        command = ("DELETE FROM %s %s %s" % (
            class_name,
            ("" if where is None else "WHERE " + where),
            ("" if limit is None else "LIMIT " + str(limit)))).strip()
        ret = self._client.command(command)
        return ret
    #end

    def delete_document(self, class_name, rid):
        """

        :param str class_name:
        :param str rid:
        :return:
        """
        command = ("DELETE FROM %s WHERE @rid = %s" % (class_name, rid)).strip()
        ret = self._client.command(command)
        return ret
    #end

    def get_document(self, class_name, rid):
        """

        :param str class_name:
        :param str rid:
        :return dict:
        """
        command = ("SELECT FROM %s WHERE @rid = %s" % (class_name, rid)).strip()
        ret = self._client.command(command)
        return ret[0] if len(ret) > 0 else None
    #end

    # =======================================================================
    # class
    # =======================================================================

    pass
# end