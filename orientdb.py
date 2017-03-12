import urllib.parse as urlp
import pyorient
import json

# ===========================================================================
# Utilities
# ===========================================================================

class URL:
    def __init__(self, url):
        self._params = dict()
        o = urlp.urlparse(url,scheme="file")

        self._params["scheme"] = o[0]  # schema
        self._params["netloc"] = o[1]  # netloc
        self._params["path"] = o[2]  # path
        self._params["params"] = o[3]  # params
        self._params["query"] = o[4].replace(",", "&")  # query
        self._params["fragment"] = o[5].replace(",", "&")  # fragment

        self._params["username"] = o.username
        self._params["password"] = o.password
        self._params["host"] = o.hostname
        self._params["port"] = o.port

        params = dict()
        params.update(urlp.parse_qs(self._params["params"]))
        params.update(urlp.parse_qs(self._params["query"]))

        if "u" in params:
            params["username"] = params["u"]
            del params["u"]
        if "p" in params:
            params["password"] = params["p"]
            del params["p"]

        for k in params:
            if len(params[k]) == 1:
                params[k] = params[k][0]
            if len(params[k]) == 0:
                params[k] = None

        self._params.update(params)
    # end

    def get(self, key, default=None):
        if key not in self._params:
            return default
        if self._params[key] is None:
            return default
        if type(default) == int:
            return int(self._params[key])
        if type(default) == float:
            return float(self._params[key])
        if type(default) == bool:
            return bool(self._params[key])
        if type(default) == str:
            return str(self._params[key])
        else:
            return self._params[key]
    # end

    def __getitem__(self, key):
        return self._params[key]

    def __setitem__(self, key, value):
        self._params[key] = value

    def __contains__(self, key):
        return key in self._params

    pass
# end


def _strof(v):
    return json.dumps(v)


def _listof(l):
    if type(l) == str:
        return l
    else:
        return str.join(",", l)


def _groupbyof(glist):
    if type(glist) == str:
        return glist
    else:
        return str.join(",", glist)


def _orderbyof(olist):
    oby = ""
    for o in olist:
        if len(oby) > 0:
            oby += ","
        if type(o) == str:
            oby += o
        else:
            oby += o[0] + " " + o[1]
    return oby


def _whereof(where, params):
    """
    Replace $'{name}' with the value in 'params'

    :param str where:
    :param dict[str,Any] params:
    :return str:
    """
    if where is None or params is None:
        return where

    pos = where.find("${")
    while pos != -1:
        end = where.find("}", pos)
        name = where[pos+2:end]
        if name not in params:
            continue
        value = params[name]
        where = where[0:pos] + _strof(value) + where[end + 1:]
        pos = where.find("${")
    # end
    return where
# end


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

_otypes = {
    str: "STRING",
    float: "DOUBLE",
    int: "INTEGER",
    set: "LINKSET",
    dict: "LINKMAP",
    list: "LINKLIST"
}

def _otype(stype):
    if stype in _otypes:
        return _otypes[stype]
    else:
        return stype


def _vbodyof(body, op="SET"):
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
        set += ("%s = %s" % (name, _strof(body[name])))
    return set

def _jbodyof(body, op):
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

def _vof(v):
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
# Public utilities
# ===========================================================================

def odata(orec):
    """
    Extract the data from the OrientRecord

    :param orec:
    :type orec: OrientRecord | list[OrientRecord]
    :return dict:
    """
    if type(orec) == list:
        return [o._OrientRecord__o_storage for o in orec]
    else:
        return orec._OrientRecord__o_storage
# end


def orid(orec):
    """
    Extract the rid from the OrientRecord
    :param orec:
    :type orec: OrientRecord | list[OrientRecord]
    :return:
    """
    if type(orec) == list:
        return [o._OrientRecord__rid for o in orec]
    else:
        return orec._OrientRecord__rid
# end


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

class OrientDB:

    # -----------------------------------------------------------------------
    # Constructor
    # -----------------------------------------------------------------------

    def __init__(self, url):
        """
        :param str url: "orient://host:port/db?u=user&p=password
        """
        assert url.startswith("orient")

        self._url = URL(url)
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
    # Handle databases
    # -----------------------------------------------------------------------

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
            db_type = self._url.get("db_type")

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
    # Handle classes and properties
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

    def create_class(self, class_name, body, drop_if_exists=False):
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
        :param dict body: field definitions
        :return list:
        """
        if self.exists_class(class_name):
            if not drop_if_exists:
                return False
            else:
                self.drop_class(class_name)

        extends = body.get("extends", None)
        """:type: str"""
        abstract = body.get("abstract", False)
        """:type: str"""

        ret = []
        if class_name:
            command = ("CREATE CLASS %s%s%s" % (
                class_name,
                ("" if not extends  else " EXTENDS " + extends),
                ("" if not abstract else " ABSTRACT")) ).strip()
            ret.extend(self._client.command(command)) # [id]

        for name in body:
            if name in ["extends", "abstract"]:
                continue
            pname = "%s.%s" % (class_name, name)
            ptype = _otype(body[name])
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
        command = ("DROP CLASS %s%s" % (
            class_name,
            ("" if not unsafe else " UNSAFE"))).strip()
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
        command = ("CREATE PROPERTY %s %s%s%s" % (
            property,
            _otype(type),
            ("" if link is None else " " + link),
            ("" if not unsafe else " UNSAFE"))).strip()
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
        command = ("DROP PROPERTY %s%s" % (
            property,
            ("" if not force else " FORCE"))).strip()
        ret = self._client.command(command)
        return ret
    # end

    # -----------------------------------------------------------------------
    # Execute command
    # -----------------------------------------------------------------------

    def execute(self, command):
        return self._client.command(command)

    # -----------------------------------------------------------------------
    # Handle vertices
    # -----------------------------------------------------------------------

    # def create_class_vertex(self, class_name, body=None, drop_if_exists=False):
    #     if body is None: body = dict()
    #     if "extends" not in body: body["extends"] = "V"
    #     return self.create_class(class_name, body=body, drop_if_exists=drop_if_exists)
    # # end

    def insert_vertex(self, class_name, body=None):
        return self.create_vertex(class_name, body=body)
    # end

    def create_vertex(self, class_name, body=None):
        """
        Create a vertex (a instance of the specified class), and set the
        body with 'body'

        Note: the class MUST extends 'V'

        :param str class_name:
        :param dict body:
        :return str: rid
        """
        command = ("CREATE VERTEX %s%s" % (class_name, _jbodyof(body, " CONTENT"))).strip()
        ret = self._client.command(command)
        return orid(ret)[0]
    # end

    def delete_vertex(self, vertex, where=None, limit=None, params=None):
        """
        Delete a vertex

        :param str vertex: rid or vertex_class
        :param str where:
        :param int limit:
        :return:
        """
        command = ("DELETE VERTEX %s%s%s" % (
            vertex,
            ("" if not where else " WHERE " + _whereof(where, params)),
            ("" if not limit else " LIMIT " + str(limit)))).strip()
        ret = self._client.command(command)
        return ret
    # end

    def update_vertex(self, vertex,
                      body=None, merge=None,
                      set=None, add=None, put=None, remove=None, incr=None,
                      where=None, limit=None, params=None):
        return self.update_document(vertex,
                                    body=body,
                                    merge=merge,
                                    set=set,
                                    add=add,
                                    put=put,
                                    remove=remove,
                                    incr=incr,
                                    where=where,
                                    limit=limit,
                                    params=params)
    # end

    def select_vertex(self, class_name, where, params=None):
        return self.select_document(target=class_name, where=where, params=params)
    # end

    def exists_vertex(self, class_name, where, params=None):
        return self.exists_document(class_name, where=where, params=params)
    # end

    def get_vertex(self, class_name, rid):
        """
        :param str class_name:
        :param str rid:
        :return:
        """
        assert rid.startswith("#")
        return self.get_document(class_name, rid)
    # end

    # -----------------------------------------------------------------------
    # Handle edges
    # -----------------------------------------------------------------------

    # def create_class_edge(self, class_name, body=None, drop_if_exists=False):
    #     if body is None: body = dict()
    #     if "extends" not in body: body["extends"] = "E"
    #     return self.create_class(class_name, body=body, drop_if_exists=drop_if_exists)
    # # end

    def insert_edge(self, class_name, vfrom, vto, body=None):
        return self.create_edge(class_name, vfrom, vto, body=body)
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

        vfrom = _vof(vfrom)
        vto = _vof(vto)

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
            command = ("UPDATE EDGE %s%s" % (rid, _jbodyof(body, " CONTENT")))
            ret = self._client.command(command)
        return rid
    # end

    def delete_edge(self, vfrom, vto=None, where=None, limit=None, params=None):
        """

        Note: vfram can be a class_name, a rid (starts with "#") or a list of
        rids.

        :param str|list vfrom: (rid) or list[(rid)] or class_name
        :param str vto: (rid)
        :param str where:
        :param int limit:
        :return:
        """

        vlist = _vof(vfrom)
        if vto is not None:
            vlist = "FROM %s TO %s" % (vlist, _vof(vto))

        command = ("DELETE EDGE %s%s%s" % (
            ("" if not vlist else vlist),
            ("" if not where else " WHERE " + _whereof(where, params)),
            ("" if not limit else " LIMIT " + str(limit)))).strip()
        ret = self._client.command(command)
        return ret
    # end

    def update_edge(self, rid,
                    body=None, merge=None,
                    set=None, add=None, put=None, remove=None, incr=None,
                    where=None, limit=None, params=None):
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

        command = ("UPDATE EDGE %s%s%s%s%s%s%s%s%s%s" % (
            rid,
            ("" if set is None else _vbodyof(set, " SET")),
            ("" if incr is None else _vbodyof(set, " INCREMENT")),
            ("" if add is None else _vbodyof(set, " ADD")),
            ("" if remove is None else _vbodyof(set, " REMOVE")),
            ("" if put is None else _vbodyof(set, " PUT")),
            ("" if body is None else _jbodyof(body, " CONTENT")),
            ("" if merge is None else _jbodyof(merge, " MERGE")),
            ("" if where is None else " WHERE " + _whereof(where, params)),
            ("" if limit is None else " LIMIT " + str(limit)))).strip()
        ret = self._client.command(command)
        return ret
    # end

    def get_edge(self, class_name, rid):
        return self.get_document(class_name, rid)
    # end

    # -----------------------------------------------------------------------
    # Navigate graph
    # -----------------------------------------------------------------------

    def traverse(self, field, target=None, while_=None, maxdepth=None,
                 limit=None, strategy=None):
        command = ("TRAVERSE " % (

        )).strip()

    # -----------------------------------------------------------------------
    # Handle documents
    # -----------------------------------------------------------------------
    #
    # 'body' | 'merge' must be a object convertible in JSON format
    #

    def insert_document(self, class_name, body):
        command = ("INSERT INTO CLASS:%s%s RETURN @rid" % (
            class_name,
            _jbodyof(body, " CONTENT"))).strip()
        ret = self._client.command(command)
        return ret
    # end

    def update_document(self, rid,
                        body=None, merge=None,
                        set=None, add=None, put=None, remove=None, incr=None,
                        where=None, limit=None, params=None):
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
        :param str where:
        :param int limit:
        :return:
        """
        command = ("UPDATE %s%s%s%s%s%s%s%s%s%s" % (
            rid,
            ("" if set is None else _vbodyof(set, " SET")),
            ("" if incr is None else _vbodyof(set, " INCREMENT")),
            ("" if add is None else _vbodyof(set, " ADD")),
            ("" if remove is None else _vbodyof(set, " REMOVE")),
            ("" if put is None else _vbodyof(set, " PUT")),
            ("" if body is None else _jbodyof(body, " CONTENT")),
            ("" if merge is None else _jbodyof(merge, " MERGE")),
            ("" if where is None else " WHERE " + _whereof(where, params)),
            ("" if limit is None else " LIMIT " + str(limit)))).strip()
        ret = self._client.command(command)
        return ret
    # end

    def delete_documents(self, class_name, where=None, limit=None, params=None):
        """
        :param str class_name:
        :param str where:
        :param int limit:
        :return:
        """
        command = ("DELETE FROM %s%s%s" % (
            class_name,
            ("" if where is None else " WHERE " + _whereof(where, params)),
            ("" if limit is None else " LIMIT " + str(limit)))).strip()
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
        return None if len(ret) == 0 else ret[0]
    #end

    def select_documents(self, what=None, target=None, where=None, groupby=None,
                         orderby=None, skip=None, limit=None, query=None,
                         params=None):
        """
        :param str|list[str] what:
        :param str target:
        :param str where:
        :param dict groupby:
        :param dict orderby:
        :param int skip:
        :param int limit:
        :param str query:
        :return list:
        """
        command = ("SELECT %s%s%s%s%s%s%s%s" % (
            ("" if what is None else _listof(what)),
            ("" if target is None else " FROM " + target),
            ("" if where is None else " WHERE " + _whereof(where, params)),
            ("" if groupby is None else " GROUP BY " + _groupbyof(groupby)),
            ("" if orderby is None else " ORDER BY " + _orderbyof(orderby)),
            ("" if skip is None else " SKIP " + str(skip)),
            ("" if limit is None else " LIMIT " + str(limit)),
            ("" if query is None else query))).strip()
        ret = self._client.command(command)
        return ret
    # end

    def select_document(self, what=None, target=None, where=None, groupby=None,
                        orderby=None, skip=None, limit=None, query=None,
                        params=None):
        ret = self.select_documents(what=what, target=target, where=where,
                                    groupby=groupby, orderby=orderby,
                                    skip=skip, limit=limit, query=query,
                                    params=params)
        return None if len(ret) == 0 else ret[0]
    # end

    def exists_document(self, target=None, where=None, skip=None, query=None,
                        params=None):
        ret = self.select_documents(target=target,where=where,
                                    skip=skip, limit=1,query=query,
                                    params=params)
        return len(ret) > 0
    # end


    # -----------------------------------------------------------------------
    # Handle indices
    # -----------------------------------------------------------------------

    def create_index(self, class_field, index_type=None, metadata=None):
        """

        :param str class_field:
        :param str index_type: UNIQUE | NOTUNIQUE
        :param dict metadata:
        """

        # UNIQUE
        # NOTUNIQUE

        command = ("CREATE INDEX %s%s%s" % (
                class_field,
                ("" if index_type is None else " " + index_type),
                ("" if metadata is None else _jbodyof(metadata, " METADATA")))).strip()
        ret = self._client.command(command)
        return ret
    # end

    def drop_index(self, index_name):
        """
        :param str index_name:
        """
        command = ("DROP INDEX %s" % index_name).strip()
        ret = self._client.command(command)
        return ret
    #end

    def rebuild_index(self, index_name):
        """
        :param str index_name:
        """
        command = ("REBUILD INDEX %s" % index_name).strip()
        ret = self._client.command(command)
        return ret
    #end

    # -----------------------------------------------------------------------
    # Handle indices
    # -----------------------------------------------------------------------

    pass
# end
