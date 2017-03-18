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
        self._session = None
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
        self._session = self._driver.session()
    # end

    def close(self):
        if self._session:
            self._session.close()
            self._session = None
    # end

    # -----------------------------------------------------------------------
    # Nodes and edges
    # -----------------------------------------------------------------------

    def create_node(self, class_name, body=None, alias=None):
        command = "CREATE (%s:%s %s)" % (
            ("" if alias is None else alias),
            class_name,
            _bodyof(body)
        )
        return self._session.run(command)
    # end

    def create_edge(self, label, vfrom, vto):
        pass

    # -----------------------------------------------------------------------
    # Match
    # -----------------------------------------------------------------------

    def match(self, command):
        return self._session.run(command)


    # -----------------------------------------------------------------------
    # End
    # -----------------------------------------------------------------------

    pass
# end