import urllib.parse as urlp
from neo4j.v1 import GraphDatabase, basic_auth

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

def _strof(o):
    if o is None:
        return "null"
    t = type(o)
    if t in [float, int]:
        return str(o)
    if t == str:
        o = o.replace("\\", "\\\\").replace("\"", "\\\"")
        return "\"%s\"" % o
    if t == bool:
        return "true" if o else "false"
    if t == list:
        return "[%s]" % str.join(",", map(_strof, o))
# end

def _bodyof(body):
    if type(body) == tuple:
        return ":%s%s" % (
            body[0],
            _bodyof(body[1])
        )
    if len(body) == 0:
        return ""
    b = "{"
    for n in body:
        if len(b) > 1:
            b += ", "
        v = _strof(body[n])
        b += "%s:%s" % (n, v)
    # end
    b += "}"
    return b
# end

# ===========================================================================
# Public utilities
# ===========================================================================

class Relation(object):

    def __init__(self, match, rel_name=None, alias=None,steps=None):
        self._from = match
        self._name = rel_name
        self._alias = alias
        self._steps = steps
        self._to = None
    # end

    def steps(self, steps):
        self._steps = steps
        return self
    # end

    def match(self, class_name=None, alias=None):
        self._to = Match(class_name=class_name, alias=alias).from_rel(self)
        return self._to
    # end

    def __str__(self):
        return ("%s-%s-" % (
            str(self._from),
            self._srel(),
            # str(self._to)
        ))

    def _srel(self):
        if self._name is None and self._alias is None:
            return ""
        else:
            return ("[%s%s]" % (
                ("" if self._alias is None else self._alias),
                ("" if self._name is None else ":" + self._name)
            ))

    pass
# end


class Result(object):

    def __init__(self, match, what):
        self._match = match
        self._what = what
    # end

    def __str__(self):
        smatch = str(self._match)
        swhat = self._what
        return ("MATCH %s RETURN %s" % (
                smatch,
                swhat
        ))

class Match(object):

    def __init__(self, class_name=None, alias=None):
        self._name = class_name
        self._alias = alias
        self._body = dict()
        self._from = None
    # end

    def field(self, name, value):
        self._body[name] = value
        return self

    def relation(self, rel_name=None, alias=None, steps=None):
        return Relation(self, rel_name=rel_name, alias=alias, steps=steps)

    def from_rel(self, relation):
        self._from = relation
        return self
    # end

    def return_(self, what):
        return Result(self, what)

    def __str__(self):
        return "%s(%s%s%s)" % (
            ("" if self._from is None else str(self._from)),
            ("" if self._alias is None else self._alias),
            ("" if self._name is None else ":" + self._name),
            ("" if self._body is None else _bodyof(self._body))
        )

    pass
# end

# ===========================================================================
# Neo4jDB
# ===========================================================================

class Neo4jDB:

    # -----------------------------------------------------------------------
    # Constructor
    # -----------------------------------------------------------------------

    def __init__(self, url):
        assert url.startswith("neo4j:") or url.startswith("bolt:")

        self._url = _url(url)
        self._driver = None
        self._client = None
    # end

    # -----------------------------------------------------------------------
    # Constructor
    # -----------------------------------------------------------------------

    def connect(self, user=None, password=None):
        if user is None:
            user = self._url["username"]
            password = self._url["password"]

        url = "bolt://{0}".format(self._url["netloc"])
        self._driver = GraphDatabase.driver(url, auth=(user, password))
        self._client = self._driver.session()
    # end

    def close(self):
        if self._client:
            self._client.close()
            self._client = None
    # end

    # -----------------------------------------------------------------------
    # Database
    # -----------------------------------------------------------------------

    def open_db(self, db_name=None, db_type=None, user=None, password=None):
        self.connect(user=user, password=password)
    # end

    def close_db(self):
        pass
    # end

    # -----------------------------------------------------------------------
    # Database
    # -----------------------------------------------------------------------

    def list_classes(self, full=False):
        command = "MATCH (n) RETURN distinct labels(n)"
        ret = self._client.run(command)
        labels = set()
        for rec in ret:
            labels.update(rec["labels(n)"])
        return list(labels)
    # end

    def exists_class(self, class_name):
        command = "MATCH (n:%s) RETURN n LIMIT 1" % class_name
        ret = self._client.run(command)
        return len(list(ret)) > 0
    # end

    def create_class(self, class_name, body, drop_if_exists=False):
        pass

    def drop_class(self, class_name, unsafe=False):
        pass

    # -----------------------------------------------------------------------

    def list_properties(self, class_name, full=False):
        command = "MATCH (n:%s) RETURN keys(n) LIMIT 1" % class_name
        ret = self._client.run(command)
        props = set()
        for rec in ret:
            props.update(rec["keys(n)"])
        return list(props)
    # end

    def create_property(self, property, type, link=None, unsafe=False):
        pass

    def drop_property(self, property, force=False):
        pass

    # -----------------------------------------------------------------------
    # Nodes and edges
    # -----------------------------------------------------------------------

    def exists_node(self, target=None, where=None, skip=None, query=None, params=None):
        command = ("MATCH (n:%s %s) RETURN n LIMIT 1" % (
            target,
            ("" if not where else _bodyof(where))
        ))
        ret = self._client.run(command)
        return len(ret) > 0
    # end

    def create_node(self, class_name, body=None, alias=None):
        command = ("CREATE (%s:%s %s)" % (
            ("n" if alias is None else alias),
            class_name,
            _bodyof(body)
        ))
        return self._client.run(command)
    # end

    def delete_node(self, class_name, where=None, limit=None, params=None):
        command = ("MATCH (n:%s %s) DELETE n" % (
            class_name,
            ("" if where is None else _bodyof(where))
        ))
        return self._client.run(command)
    # end

    # -----------------------------------------------------------------------

    def insert_document(self, class_name, body=None, alias=None):
        return self.create_node(class_name, body=body, alias=alias)

    def delete_document(self, class_name, where=None, limit=None, params=None):
        return self.delete_node(class_name, where=where, limit=limit, params=params)

    # -----------------------------------------------------------------------

    def create_edge(self, label, vfrom, vto, body=None, undirect=False, multiple=False):
        retf = rett = None
        if True:
            command = ("MATCH (f%s),(t%s) CREATE (f)-[r:%s%s]->(t)" % (
                _bodyof(vfrom),
                _bodyof(vto),
                label,
                ("" if not body else _bodyof(body))
            ))
            retf = list(self._client.run(command))
        if undirect:
            command = (
            "MATCH (f%s),(t%s) CREATE (f)<-[r:%s%s]-(t)" % (
                _bodyof(vfrom),
                _bodyof(vto),
                label,
                ("" if not body else _bodyof(body))
            ))
            rett = list(self._client.run(command))
        else:
            rett = []

        return retf.extend(rett)
    # end

    # -----------------------------------------------------------------------
    # Execute command
    # -----------------------------------------------------------------------

    @property
    def client(self):
        return self._client

    def execute(self, command):
        return self._client.run(command)

    # -----------------------------------------------------------------------
    # Match
    # -----------------------------------------------------------------------

    def match(self, match):
        command = str(match)
        print(command)
        return self._client.run(command)


    # -----------------------------------------------------------------------
    # End
    # -----------------------------------------------------------------------

    pass
# end