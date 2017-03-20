from path import Path
import re as rexp
import snowballstemmer as sbs
import gensim.corpora as corpora
import gensim.models as models

# ===========================================================================
#
# ===========================================================================

class StopWords(object):
    """
    Handle the stopwords
    """

    def __init__(self):
        self._swords = set()

    def load_stopwords(self, swfile):
        """
        Load the file of stopwords.

        Comments can follow #
        The words must be sapared by space or newline.

        :param str swfile: path of the file to load
        """
        self._swords = set()

        if swfile is None:
            return
        with open(swfile, encoding="utf-8", mode="r") as f:
            for line in f:
                sc = line.find("#")
                line = line[0:sc] if sc != -1 else line
                if line.startswith("#") or len(line) == 0:
                    continue
                for w in line.split():
                    self._swords.add(w.lower())
            pass
            f.close()
        pass
    pass

    def is_sw(self, w):
        """Check if the word is a stopword"""
        return w in self._swords

    pass
pass


class StemRules(object):
    """
    Simple stemmer: used to convert plural words in singulare and female words in male
    Uses a simple dictionary
    """

    def __init__(self, N=8):
        """
        Create the object
        :param int N: max length of the suffix used in the rules
        """
        self.N = N
        self._rules = [None]*(N+1)
        self._stemmer = sbs.stemmer('italian')
    pass

    def load_stemrules(self, stfile):
        """
        Load th fie of rules

        :param str stfile:  path of the file to load
        """

        N = self.N
        self._rules = [None]*(N+1)

        if stfile is None:
            return

        with open(stfile) as f:
            for line in f:
                line = line.strip()
                if len(line) == 0 or line.startswith("#"):
                    continue
                try:
                    p = line.index(':')
                    suffix = line[0:p].strip()
                    replace = line[p+1:].strip()
                    self._add_rule(suffix, replace)
                except:
                    pass
            pass
            f.close()
        pass
    pass

    def _add_rule(self, suffix, replace):
        n = len(suffix)

        if self._rules[n] is None:
            self._rules[n] = dict()

        self._rules[n][suffix] = replace
    pass

    def normalize(self, w):
        """
        Normalize the word

        :param str w: the word to normalize
        :return str: the normalized word
        """
        #
        # Nota: usa lo stemmer, porting da:
        #
        #   http://snowball.tartarus.org/
        #
        # Problema: lo stemmer tronca le parole.
        #           Invece si vorrebbe trasformare le parole (eventualmente anche con errori,
        #           non sarebbe un problema:
        #
        #           plurale -> singolare
        #           femminile -> maschile
        #           tempo verbale -> infinito
        #
        # return self._stemmer.stemWord(w)

        n = len(w)
        N = min(n, self.N)
        for i in range(N, 0, -1):
            rdict = self._rules[i]
            if rdict is None:
                continue
            suffix = w[n - i:]
            if suffix not in rdict:
                continue
            w = w[0:n - i] + rdict[suffix]
        pass
        return w
    pass

    pass
pass


class Synonimous:
    def __init__(self):
        self._wddict = dict()
        self._sydict = dict()
        pass

    def load_synonimous(self, syfile):
        self._wddict = dict()
        self._sydict = dict()
        self._wset = set()

        if syfile is None:
            return

        print("Loading synonimous ...")

        word = "$begin"
        synonimous = []
        with open(syfile, mode="r") as f:
            for line in f:

                #
                # if the line start with a "(" is a line with synonymous of
                # a previous word
                if line.startswith("("):
                    syn = self._analyze_synonimous(line)
                    synonimous.extend(syn)
                else:
                    self._register(word, synonimous)
                    word = self._analyze_word(line)
                    synonimous = []
                    print(" ... analyzing '%s'" % word)
                    pass
                pass
            pass
            # last word
            self._register(word, synonimous)
        pass
    pass

    def dump(self, prefix=""):
        sd = self._sydict
        for w in sd:
            if w.startswith(prefix):
                print("... {0}:\n... ... {1}".format(w, str(sd[w])))
    pass


    def _register(self, word, synonimous):
        # if len(synonimous) == 0:
        #     return
        self._wddict[word] = synonimous

        for syn in synonimous:
            if syn not in self._sydict:
                self._sydict[syn] = set()
            self._sydict[syn] = self._sydict[syn].union(synonimous)

        self._wset.add(word)
        self._wset.update(synonimous)
    pass

    def _analyze_word(self, line):
        #
        # abbacinare|1
        #
        parts = line.split("|")
        return parts[0].strip()
    pass

    def _analyze_synonimous(self, line):
        # (v.   )
        # (s.m. ...)
        # (s.f. ...)
        # (agg. ...)
        # (avv. ...)

        parts = line.split("|")
        if not (parts[0].startswith("(.") or
            parts[0].startswith("(cong.") or
            parts[0].startswith("(prep.") or
            parts[0].startswith("(inter.") or
            parts[0].startswith("(v.") or
            parts[0].startswith("(s.m.") or
            parts[0].startswith("(s.f.") or
            parts[0].startswith("(agg.") or
            parts[0].startswith("(avv.")):
            print("... unknown prefix %s" % parts[0])
            pass
        return [s.strip() for s in parts[1:]]
    pass

    def __getitem__(self, w):
        try:
            return self._sydict[w]
        except:
            return []

    def __missing__(self, w):
        return []

    def __iter__(self):
        return self._wset.__iter__()
pass


# ===========================================================================
#
# ===========================================================================

class Topic:

    # -----------------------------------------------------------------------
    # Constructor
    # -----------------------------------------------------------------------

    def __init__(self, topics, root):
        """

        :param Topics topics:
        :param Path root:
        """
        self._topics = topics
        self._root = root

        self._info = self._root.joinpath("topic.info")
        """:type: Path"""

        self._name = str(root.name)
        """:type: str"""

        self._corpus = None
        """:type: list[list[]]"""

        self._dict = corpora.Dictionary()
        """:type: corpora.Dictionary"""

        self._lda = None
        """:type: models.LdaMulticore"""
        self._lsi = None
        """:type: models.LsiModel"""
        self._hdp = None
        """:type: models.HdpModel"""
    pass

    # -----------------------------------------------------------------------
    # Properties
    # -----------------------------------------------------------------------

    @property
    def name(self):
        return self._name

    # -----------------------------------------------------------------------
    # load_documents
    # -----------------------------------------------------------------------

    def compose_corpus(self):
        print("[%s] Compose corpus ..." % self._name)
        topics = self._topics

        self._corpus = []
        for pattern in topics._patterns:
            for file in self._root.files(pattern=pattern):
                bow = self._load_file(file, allow_update=True)
                self._corpus.append(bow)
            pass
        pass

        print("... create models ...")
        self._lda = models.LdaMulticore(self._corpus, id2word=self._dict, num_topics=100)
        self._lsi = models.LsiModel(self._corpus, id2word=self._dict, num_topics=100)
        self._hdp = models.HdpModel(self._corpus, id2word=self._dict)
    pass

    def save_corpus(self, directory=None):
        print("[%s] Save corpus ..." % self._name)
        name = self._name

        dir = "%s/" % (directory if directory else ".")

        self._lda.save(dir + name + ".lda")
        self._lsi.save(dir + name + ".lsi")
        self._hdp.save(dir + name + ".hdp")
        self._dict.save_as_text(dir + name + ".dict")
        corpora.BleiCorpus.serialize(dir + name + ".blei", self._corpus)
    pass

    def load_corpus(self, directory=None):
        print("[%s] Load corpus ..." % self._name)
        name = self._name

        dir = "%s/" % (directory if directory else ".")

        self._dict = corpora.Dictionary.load_from_text(dir + name + ".dict")
        self._lda = models.LdaMulticore.load(dir + name + ".lda")
        self._lsi = models.LsiModel.load(dir + name + ".lsi")
        self._hdp = models.HdpModel.load(dir + name + ".hdp")
        self._corpus = corpora.BleiCorpus(self._corpus, dir + name + ".blei")
    pass

    def _load_file(self, filepath, allow_update=False):
        topics = self._topics

        print("... file '%s'" % filepath.name)
        doc = []
        with open(filepath, encoding="utf-8", mode="r") as f:
            for line in f:
                words = topics.text_to_words(line)
                doc.extend(words)
            pass
            f.close()
        pass
        return self._doc2bow(doc, allow_update=allow_update)
    pass

    def _doc2bow(self, words, allow_update=False):
        return self._dict.doc2bow(words, allow_update=allow_update)
    pass

    # -----------------------------------------------------------------------
    # topic_for_bow
    # -----------------------------------------------------------------------

    def topic_for_words(self, words):
        print("[%s] Compare with documents ..." % self._name)

        bow = self._doc2bow(words)

        lda = self._lda[bow]
        lsi = self._lsi[bow]
        hdp = self._hdp[bow]

        return {"lda": lda, "lsi": lsi, "hdp": hdp}
    pass

    # -----------------------------------------------------------------------
    # End
    # -----------------------------------------------------------------------

pass


class Topics:

    # -----------------------------------------------------------------------
    # Constructor
    # -----------------------------------------------------------------------

    def __init__(self, root=None, directory=None, pattern="*.txt",
                 re="[^A-Za-zàáèéìíòóùú]",
                 stopwords=None, stemrules=None, minlen=1):
        """
        Initialize the Topics manager
        :param str|list root: root directory or list of root directories
        :param str|list[str] pattern: list of file patterns to select
        :param str re: regular expression used to split the file
        :param str stopwords: file with the list of stopwords
        :param str stemrules: file with stem rules
        :param int minlen: minimum length of the words
        """
        if root is not None:
            if type(root) == str:
                root = [root]
            directory = []
            for r in root:
                r = Path(r)
                directory.extend([str(d) for d in r.dirs()])
            pass
        pass

        if type(directory) == str:
            directory = [directory]

        if type(pattern) != list:
            pattern = [pattern]

        if not directory:
            directory = []

        self._directories = [Path(d) for d in directory]
        """:type: list[Path]"""

        self._topics = list()
        """:type: list[Topic]"""

        self._patterns = pattern
        """:type: list[str]"""

        self._re = re
        """:type: str"""

        self._mlen = minlen
        """:type: int"""

        self._stopw = StopWords()
        """:type: StopWords"""

        self._stemr = StemRules()
        """:type: StemRules"""

        self._stopwordfile = Path(stopwords) if stopwords else None
        """:type: Path"""

        self._stemrulefile = Path(stemrules) if stemrules else None
        """:type: Path"""

        self._initialize()
    pass

    def _initialize(self):
        # self._corpus_dict = corpora.Dictionary()
        # load the stopword file
        self._stopw.load_stopwords(self._stopwordfile)
        # load the stemmer rules file
        self._stemr.load_stemrules(self._stemrulefile)
        # define the topics
        for d in self._directories:
            topic = Topic(self, d)
            name = topic.name
            self._topics.append(topic)
        pass
    pass

    # -----------------------------------------------------------------------
    # Properties
    # -----------------------------------------------------------------------

    @property
    def topics(self):
        """
        List of defined topics

        :return iter[str]:
        """
        return [t.name for t in self._topics]
    pass

    # -----------------------------------------------------------------------
    # Corpora
    # -----------------------------------------------------------------------

    def compose_corpora(self):
        """
        Load the documents in the directories specified by topics
        """
        # load the documents in each topic and create the dictionary
        for t in self._topics:
            t.compose_corpus()
    pass

    def save_corpora(self, directory=None):
        """
        Save corpora for each topic
        """
        print("Save corpora ...")
        for t in self._topics:
            t.save_corpus(directory=directory)
    pass

    def load_corpora(self, directory=None):
        """
        Load the corpora related to each topic
        """
        print("Load corpora ...")
        for t in self._topics:
            t.load_corpus(directory=directory)
    pass

    # -----------------------------------------------------------------------
    # Implementation
    # -----------------------------------------------------------------------

    def file_to_words(self, filepath):
        words = []
        with open(filepath) as f:
            for line in f:
                for w in rexp.split(self._re, line):
                    w = self._normalize(w)
                    if self._valid(w):
                        words.append(w)
                pass
            pass
        pass
        return words
    pass

    # -----------------------------------------------------------------------

    def text_to_words(self, text):
        """
        Split the text in a list of words and normalize the words

        :param str text: text to parse
        :return list[str]: list of owrds
        """
        words = []
        for w in rexp.split(self._re, text):
            w = self._normalize(w)
            if self._valid(w):
                words.append(w)
        pass
        return words
    pass

    # -----------------------------------------------------------------------
    # Topics selection
    # -----------------------------------------------------------------------

    def topic_for_text(self, text):
        words = self.text_to_words(text)
        return self.topic_for_words(words)
    pass

    def topic_for_file(self, filepath):
        words = self.file_to_words(filepath)
        return self.topic_for_words(words)
    pass

    def topic_for_words(self, words):
        tdict = dict()

        for t in self._topics:
            assert isinstance(t, Topic)
            tname = t.name
            tweight = t.topic_for_words(words)

            tdict[tname] = tweight
        pass
        return tdict
    pass

    # -----------------------------------------------------------------------
    # Implementation
    # -----------------------------------------------------------------------

    def _normalize(self, w):
        w = w.lower()
        w = self._stemr.normalize(w)
        return w
    pass

    #
    # check if the word is valid
    #
    def _valid(self, w):
        if len(w) < self._mlen:
            return False
        if self._stopw.is_sw(w):
            return False
        return True
    pass

    # -----------------------------------------------------------------------
    # End
    # -----------------------------------------------------------------------

pass


# ===========================================================================
#
# ===========================================================================
