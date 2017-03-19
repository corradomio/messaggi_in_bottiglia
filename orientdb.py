import urllib.parse as urlp
import pyorient
import json

# ===========================================================================
# Utilities
# ===========================================================================

class _url:
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
    """
    Create a string from the object using the JSON syntax

    :param Any v:
    :return str:
    """
    return json.dumps(v)


def _listof(l):
    """
    Create a list of objects separated from ","
    :param l:
    :return:
    """
    if l is None:
        return ""
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


def _resolve_vars(where, params):
    """
    Replace $'{name}' with the value in 'params'
    If name is not in 'params' replace with the empty string ""

    :param str where:
    :param dict[str,Any] params:
    :return str:
    """
    if params is None:
        params = dict()
    if where is None or len(where) == 0:
        return where

    if type(where) == str:
        if len(params) == 0:
            return where
        else:
            pos = where.find("${")
            while pos != -1:
                end = where.find("}", pos)
                name = where[pos + 2:end]
                if name not in params:
                    value = ""
                else:
                    value = params[name]
                where = where[0:pos] + _strof(value) + where[end + 1:]
                pos = where.find("${")
            # end
            return where
        # end
    # end

    if type(where) == dict:
        swhere = ""
        for name in where:
            if len(swhere) > 0: swhere += " AND "
            swhere += ("%s=%s" % (name, _strof(where[name])))
        return swhere
    # end
    return where
# end


def _funof(fun):
    if fun.startswith("-") or fun.endswith("-"):
        return fun
    if not fun.endswith(")"):
        fun += "()"
    if not fun.startswith("."):
        fun = "." + fun
    return fun


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
    """
    Convert a Python type in a OrientDB type
    :param stype:
    :return:
    """
    if stype in _otypes:
        return _otypes[stype]
    else:
        return stype


def _vbodyof(body, op):
    """
    Convert body (a dictionary) in a list of type:

        op name = value, ...

    :param dict body:
    :param str op: operation
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
    Convert body (a dictionary) in a JSON serialized string

        op JSON

    :param dict body:
    :param str op: operation
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
    Convert:

        #rid  ->  #rid
        list  ->  '[' list[0] ',' ... ']'
        str   ->  '(' str ')'
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


class _Expr:
    def __init__(self, sep=","):
        self._text = ""
        self._sep = sep
        self._rest = False
    # end

    def part(self, e):
        if e and len(e) > 0:
            if self._rest:
                self._text += ",%s" % e
            else:
                self._text += e
            self._rest = True
        return self
    # end

    def strip(self):
        return self._text
# end

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


#
#
#  V - out()  -> V
#  V - outE() -> E
#  E - outV() -> V

class Match(object):
    def __init__(self, body=None, params=None):
        if body is None:
            body = dict()
        self._body=[dict(body)]
        self._params = dict() if params is None else params
        self._result = None
        self._limit = None
    pass

    def vertex(self, vclass, alias=None):
        n = len(self._body)-1
        self._body[n]["class"] = vclass
        if alias:
            self._body[n]["as"] = alias
        return self

    def where(self, where, params=None):
        if params is None:
            params = self._params
        n = len(self._body)-1
        self._body[n]["where"] = _resolve_vars(where, params)
        return self

    def while_(self, while_, params=None):
        if params is None:
            params = self._params
        n = len(self._body)-1
        self._body[n]["while"] = _resolve_vars(while_, params)
        return self

    def maxDepth(self, maxDepth):
        n = len(self._body)-1
        self._body[n]["maxDepth"] = maxDepth
        return self

    def optional(self, optional):
        n = len(self._body)-1
        self._body[n]["optional"] = "true" if optional else "false"
        return self


    def out(self, body=None, vclass=None):
        if body is None:
            body = dict()
        body = dict(body)
        body["fun"] = ".out(%s)" % _listof(vclass)
        self._body.append(body)
        return self
    pass

    def in_(self, body=None, vclass=None):
        if body is None:
            body = dict()
        body = dict(body)
        body["fun"] = ".in(%s)" % vclass
        self._body.append(body)
        return self
    pass

    def both(self, body=None, vclass=None):
        if body is None:
            body = dict()
        body = dict(body)
        body["fun"] = ".both(%s)" % _listof(vclass)
        self._body.append(body)
        return self
    pass

    def out_v(self, body=None, vclass=None):
        if body is None:
            body = dict()
        body = dict(body)
        body["fun"] = ".outV(%s)" % _listof(vclass)
        self._body.append(body)
        return self
    pass

    def in_v(self, body=None, vclass=None):
        if body is None:
            body = dict()
        body = dict(body)
        body["fun"] = ".inV(%s)" % _listof(vclass)
        self._body.append(body)
        return self
    pass

    def both_v(self, body=None, vclass=None):
        if body is None:
            body = dict()
        body = dict(body)
        body["fun"] = ".bothV(%s)" % _listof(vclass)
        self._body.append(body)
        return self
    pass

    def out_e(self, body=None, eclass=None):
        if body is None:
            body = dict()
        body = dict(body)
        body["fun"] = ".outE(%s)" % _listof(eclass)
        self._body.append(body)
        return self
    pass

    def in_e(self, body=None, eclass=None):
        if body is None:
            body = dict()
        body = dict(body)
        body["fun"] = ".inE(%s)" % _listof(eclass)
        self._body.append(body)
        return self
    pass

    def both_e(self, body=None, eclass=None):
        if body is None:
            body = dict()
        body = dict(body)
        body["fun"] = ".bothE(%s)" % _listof(eclass)
        self._body.append(body)
        return self
    pass

    def result(self, rexp, alias=None):
        if type(rexp) == list:
            self._result = rexp
        else:
            if self._result is None:
                self._result = []
            if alias:
                self._result.append((rexp, alias))
            else:
                self._result.append(rexp)
        return self
    pass

    def limit(self, limit):
        self._limit = limit
        return self
    pass

    def compose(self):

        match_ = ""
        for body in self._body:
            part_ = _Expr() \
            .part("" if "class" not in body else " class:" + body["class"]) \
            .part("" if "as" not in body else " as: " + body["as"]) \
            .part("" if "where" not in body else " where: (%s)" % body["where"]) \
            .part("" if "while" not in body else " while: (%s)" % body["while"]) \
            .part("" if "maxDepth" not in body else " maxDepth: " + str(body["maxDepth"])) \
            .part("" if "optional" not in body else " optional: " + _strof(body["optional"])) \
            .strip()
            match_ += ("%s{%s}" % (
                ("" if "fun" not in body else body["fun"]),
                part_
            ))
        # end

        return_ = _Expr()
        for ret in self._result:
            if type(ret) == tuple:
                return_.part("%s AS %s" % ret)
            else:
                return_.part(ret)
        # end
        return_ = return_.strip()

        command = ("MATCH %s RETURN %s%s" % (
            match_,
            return_,
            ("" if self._limit is None else " LIMIT " + str(self._limit))
        )).strip()
        return command
    # end
# end


# ===========================================================================
# OrientDB
# ===========================================================================
#
# Simple wrapper of 'pyorient.client' to simplify the major operations
#
# There are 2 group of operations:
#
# 1) create a connection to the server AND list the existent databases,
#    create a new database, destroy a database, etc
# 2) create a connection to the server AND select a specific database,
#    create classes, insert, update delete instances, navigate the graph
#
# The values for the command are more flexible dictionaries
#

#
# Nota: !!!!!
# E' inutile creare due tipi di oggetti distinti tra 'document' e 'vertex'
#

class OrientDB:

    # -----------------------------------------------------------------------
    # Constructor
    # -----------------------------------------------------------------------

    def __init__(self, url):
        """
        :param str url: "orient://host:port/db?u=user&p=password
        """
        assert url.startswith("orient:")

        self._url = _url(url)
        self._client = None
        self._session = None
        self._db = None
        self._is_graph = False

        host = self._url["host"]
        port = self._url.get("port", 2424)
        self._is_graph = pyorient.DB_TYPE_GRAPH == self._url.get("db_type", None)

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

    def is_graph(self):
        return self._is_graph

    # -----------------------------------------------------------------------
    # Handle database
    # -----------------------------------------------------------------------

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

        self._db = self._client.db_open(
            db_name=db_name, db_type=db_type,
            user=user, password=password)

        self._is_graph = pyorient.DB_TYPE_GRAPH == db_type
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
        self._db_type = None
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
        if self._is_graph and "extends" not in body:
            body["extends"] = "V"
        return self._create_class(class_name, body, drop_if_exists=drop_if_exists)
    # end

    def _create_class(self, class_name, body, drop_if_exists=False):
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
                ("" if not abstract else " ABSTRACT")
            )).strip()
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
            ("" if not unsafe else " UNSAFE")
        )).strip()
        ret = self._client.command(command)  # [True]
        return ret
    # end

    # -----------------------------------------------------------------------

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
            ("" if not unsafe else " UNSAFE")
        )).strip()
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
            ("" if not force else " FORCE")
        )).strip()
        ret = self._client.command(command)
        return ret
    # end

    # -----------------------------------------------------------------------
    # Execute command
    # -----------------------------------------------------------------------

    @property
    def client(self):
        return self._client

    def execute(self, command):
        return self._client.command(command)

    def query(self, skip=None, limit=None, *args):
        return self._client.query(*args)

    def gremlin(self, *args):
        return self._client.gremlin(*args)

    # -----------------------------------------------------------------------
    # Handle vertices
    # -----------------------------------------------------------------------

    def _create_vertex(self, class_name, body=None):
        """
        Create a vertex (a instance of the specified class), and set the
        body with 'body'

        Note: the class MUST extends 'V'

        :param str class_name:
        :param dict body:
        :return str: rid
        """
        command = ("CREATE VERTEX %s%s" % (
            class_name, _jbodyof(body, " CONTENT")
        )).strip()
        ret = self._client.command(command)
        return ret[0]._rid
    # end

    def _delete_vertex(self, vertex, where=None, limit=None, params=None):
        """
        Delete a vertex

        :param str vertex: rid or vertex_class
        :param str where:
        :param int limit:
        :return:
        """
        command = ("DELETE VERTEX %s%s%s" % (
            vertex,
            ("" if not where else " WHERE " + _resolve_vars(where, params)),
            ("" if not limit else " LIMIT " + str(limit))
        )).strip()
        ret = self._client.command(command)
        return ret
    # end

    # -----------------------------------------------------------------------
    # Handle edges
    # -----------------------------------------------------------------------

    def exists_edge(self, class_name, vfrom, vto, direct=False):
        command = ("SELECT FROM %s WHERE %s(%s).@rid CONTAINS %s" % (
            vfrom,
            ("out" if direct else "both"),
            ("" if class_name is None else class_name),
            vto
        ))
        ret = self._client.command(command)
        return ret
    # end

    def create_edge(self, class_name, vfrom, vto, body=None, undirect=False, multiple=False):
        if not multiple:
            ret = self.exists_edge(class_name, vfrom, vto)
            if ret:
                return ret

        ret = self._create_edge(class_name, vfrom, vto, body=body)
        return ret
    # end

    def _create_edge(self, class_name, vfrom, vto, body=None):
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
            vto
        )).strip()
        ret = self._client.command(command)
        rid = ret[0]._rid

        #
        # A quanto sempbra, NON FUNZIONA creare un edge e impostare direttamente
        # il body. Soluzione: 2 passi
        #
        if body:
            command = ("UPDATE EDGE %s%s" % (rid, _jbodyof(body, " CONTENT")))
            ret = self._client.command(command)
        return ret
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
        if vto:
            vlist = "FROM %s TO %s" % (vlist, _vof(vto))

        command = ("DELETE EDGE %s%s%s" % (
            ("" if not vlist else vlist),
            ("" if not where else " WHERE " + _resolve_vars(where, params)),
            ("" if not limit else " LIMIT " + str(limit))
        )).strip()
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
            ("" if where is None else " WHERE " + _resolve_vars(where, params)),
            ("" if limit is None else " LIMIT " + str(limit))
        )).strip()
        ret = self._client.command(command)
        return ret
    # end

    def get_edge(self, class_name, rid):
        return self.get_document(class_name, rid)
    # end

    # -----------------------------------------------------------------------
    # Navigate the graph
    # -----------------------------------------------------------------------

    def traverse(self, start, target=None, where=None, maxdepth=None,
                 limit=None, strategy=None, params=None):
        command = ("TRAVERSE %s%s%s%s%s%s" % (
            start,
            ("" if target is None else " FROM " + target),
            ("" if maxdepth is None else " MAXDEPTH " + str(maxdepth)),
            ("" if where is None else " WHILE " + _resolve_vars(where, params)),
            ("" if limit is None else " LIMIT " + str(limit)),
            ("" if strategy is None else " STRATEGY " + strategy)
        )).strip()
        ret = self._client.command(command)
        return ret
    # end

    # MATCH
    #   {
    #     [class: <class>],
    #     [as: <alias>],
    #     [where: (<whereCondition>)]
    #   }
    #   .<functionName>(){
    #     [class: <className>],
    #     [as: <alias>],
    #     [where: (<whereCondition>)],
    #     [while: (<whileCondition>)],
    #     [maxDepth: <number>],
    #     [optional: (true | false)]
    #   }*
    # RETURN <expression> [ AS <alias> ] [, <expression> [ AS <alias> ]]*
    # LIMIT <number>
    #
    # <functionName>() ::=
    #       in()    <--     in("EdgeClass")     <-EdgeClass-
    #       out()   -->     out("EdgeClass")    -EdgeClass->
    #       both()  --      both("EdgeClass")   -EdgeClass-
    # .

    def match(self, match):
        command = match.compose()
        ret = self._client.command(command)
        return ret
    # end

    # -----------------------------------------------------------------------
    # Handle documents
    # -----------------------------------------------------------------------
    #
    # 'body' | 'merge' must be a object convertible in JSON format
    #

    def exists_node(self, target=None, where=None, skip=None, query=None, params=None):
        return self.exists_document(target=target, where=where, skip=skip, query=query, params=params)

    def create_node(self, class_name, body=None, alias=None):
        return self._create_vertex(class_name, body=body)

    def delete_node(self, class_name, where=None, limit=None, params=None):
        return self._delete_vertex(class_name, where=where, limit=limit, params=params)

    def select_nodes(self, target=None, what=None, where=None, groupby=None,
                     orderby=None, skip=None, limit=None, query=None, params=None):
        return self.select_documents(
            target=target, what=what, where=where, groupby=groupby,
            orderby=orderby, skip=skip, limit=limit, query=query, params=params)

    # -----------------------------------------------------------------------

    def insert_document(self, class_name, body=None, alias=None):
        if self._is_graph:
            return self._create_vertex(class_name, body)
        else:
            return self._insert_document(class_name, body)
    # end

    def delete_document(self, class_name, where=None, limit=None, params=None):
        if self._is_graph:
            return self._delete_vertex(class_name, where=where, limit=limit, params=params)
        else:
            return self._delete_documents(class_name, where=where, limit=limit, params=params)
    # end

    # -----------------------------------------------------------------------

    def exists_document(self, target=None, where=None, skip=None, query=None, params=None):
        ret = list(self.select_documents(target=target,where=where,
                                    skip=skip, limit=1,query=query,
                                    params=params))
        return len(ret) > 0
    # end

    def get_document(self, target=None, what=None, where=None,
                     groupby=None, orderby=None,
                     skip=None, query=None,
                     params=None):
        ret = list(self.select_documents(what=what, target=target, where=where,
                                    groupby=groupby, orderby=orderby,
                                    skip=skip, limit=1, query=query,
                                    params=params))
        return None if len(ret) == 0 else ret[0]
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
            ("" if where is None else " WHERE " + _resolve_vars(where, params)),
            ("" if limit is None else " LIMIT " + str(limit))
        )).strip()
        ret = self._client.command(command)
        return ret
    # end

    def _insert_document(self, class_name, body):
        command = ("INSERT INTO %s%s RETURN @rid" % (
            class_name,
            _jbodyof(body, " CONTENT")
        )).strip()
        ret = self._client.command(command)
        return ret
    # end

    # -----------------------------------------------------------------------

    def select_documents(self, target=None, what=None, where=None, groupby=None,
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
            ("" if where is None else " WHERE " + _resolve_vars(where, params)),
            ("" if groupby is None else " GROUP BY " + _groupbyof(groupby)),
            ("" if orderby is None else " ORDER BY " + _orderbyof(orderby)),
            ("" if skip is None else " SKIP " + str(skip)),
            ("" if limit is None else " LIMIT " + str(limit)),
            ("" if query is None else query)
        )).strip()

        if not skip:
            skip = 0

        if limit:
            ret = self._client.query(command)
            for rec in ret:
                yield rec
        else:
            limit = 25
            ret = self._client.query(command)
            while len(ret) > 0:
                for rec in ret:
                    skip += 1
                    yield rec

                ret = self._client.query(command + (" SKIP %d LIMIT %d" % (skip, limit)))
            # end
        pass
    # end

    def _delete_documents(self, class_name, where=None, limit=None, params=None):
        """
        :param str class_name:
        :param str where:
        :param int limit:
        :return:
        """
        command = ("DELETE FROM %s%s%s" % (
            class_name,
            ("" if where is None else " WHERE " + _resolve_vars(where, params)),
            ("" if limit is None else " LIMIT " + str(limit))
        )).strip()
        ret = self._client.command(command)
        return ret
    #end

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
                ("" if metadata is None else _jbodyof(metadata, " METADATA"))
        )).strip()
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
