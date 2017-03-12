from path import Path
import re as rexp
import snowballstemmer as sbs
import gensim.corpora as corpora
import gensim.models as models


# def is_list(x):
#     return isinstance(x, list)

# def flatten(l):
#     if all(map(is_list, l)):
#         return reduce(operator.add, map(flatten, l))
#     else:
#         return l
# # end


# ===========================================================================
#
# ===========================================================================

class StopWords(object):
    """
    Handle the stopwords
    """

    def __init__(self):
        self._swords = set()
    # end

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
        # end
    # end

    def is_sw(self, w):
        """Check if the word is a stopword"""
        return w in self._swords
    # end

    pass
# end


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
    # end

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
                # end
            # end
            f.close()
        # end
    # end

    def _add_rule(self, suffix, replace):
        n = len(suffix)

        if self._rules[n] is None:
            self._rules[n] = dict()

        self._rules[n][suffix] = replace
    # end

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
    # end

    pass
# end


class Synonimous:
    def __init__(self):
        self._wddict = dict()
        self._sydict = dict()
        pass

    def load_synonimous(self, syfile):
        self._wddict = dict()
        self._sydict = dict()

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
                # end
            # end
            # last word
            self._register(word, synonimous)
        # end
    # end

    def dump(self, prefix=""):
        sd = self._sydict
        for w in sd:
            if w.startswith(prefix):
                print("... {0}:\n... ... {1}".format(w, str(sd[w])))
    # end


    def _register(self, word, synonimous):
        # if len(synonimous) == 0:
        #     return
        self._wddict[word] = synonimous

        for syn in synonimous:
            if syn not in self._sydict:
                self._sydict[syn] = set()
            self._sydict[syn] = self._sydict[syn].union(synonimous)
    # end

    def _analyze_word(self, line):
        #
        # abbacinare|1
        #
        parts = line.split("|")
        return parts[0].strip()
    # end

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
    # end

    def __getitem__(self, w):
        return self._sydict[w]

    def __iter__(self):
        return self._sydict.__iter__()
# end


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

        self._hdp = None
        """:type: models.HdpModel"""
    pass

    # -----------------------------------------------------------------------
    # Properties
    # -----------------------------------------------------------------------

    @property
    def name(self):
        return self._name
    pass

    # -----------------------------------------------------------------------
    # Operations
    # -----------------------------------------------------------------------

    def load_documents(self):
        print("[%s] Load documents ..." % self._name)

        topics = self._topics

        for pattern in topics._patterns:
            for file in self._root.files(pattern=pattern):
                self._load_file(file)
    pass

    def _load_file(self, filepath):
        topics = self._topics

        print("... file '%s'" % filepath.name)
        doc = []
        with open(filepath, encoding="utf-8", mode="r") as f:
            for text in f:
                words = topics.text_to_words(text)
                doc.extend(words)
            pass
            f.close()
        pass
        return topics.doc2bow(doc, allow_update=True)
    pass

    # -----------------------------------------------------------------------
    #
    # -----------------------------------------------------------------------

    def extract_topics(self, n_topics=None):
        print("[%s] Analyze documents ..." % self._name)
        topics = self._topics

        corpus = []
        for pattern in topics._patterns:
            for file in self._root.files(pattern=pattern):
                bow = self._load_file(file)
                corpus.append(bow)
        pass

        if n_topics is None:
            n_topics=self._guess_topics(corpus)

        dictionary = topics._corpus_dict

        self._hdp = models.HdpModel(corpus, id2word=dictionary)

    pass

    def _guess_topics(self, corpus):
        nwords = len(flatten(corpus))
        return 100
    pass

    def save_topics(self, topics=None):
        pass
    pass
    def load_topics(self, topics=None):
        pass
    pass

    # -----------------------------------------------------------------------
    # End
    # -----------------------------------------------------------------------
# end


class Topics:

    # -----------------------------------------------------------------------
    # Constructor
    # -----------------------------------------------------------------------

    def __init__(self,
                 root=None,
                 directory=None,
                 pattern="*.txt",
                 re="[^A-Za-zàáèéìíòóùú]",
                 stopwords=None,
                 stemrules=None,
                 minlen=1):
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

        self._directories = [Path(d) for d in directory]
        """:type: list[Path]"""

        self._topics = dict()
        """:type: dict[str,Topic]"""

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


        self._corpus_dict = corpora.Dictionary()
        """:type: corpora.Dictionary"""
    pass

    # -----------------------------------------------------------------------
    # Properties
    # -----------------------------------------------------------------------

    @property
    def topics(self):
        """
        :return iter[str]:
        """
        return self._topics.keys()
    pass

    # -----------------------------------------------------------------------
    # Dictionary
    # -----------------------------------------------------------------------

    def load_documents(self):
        self._topics = dict()
        """:type: dict[str,Topic"""

        self._stopw.load_stopwords(self._stopwordfile)
        self._stemr.load_stemrules(self._stemrulefile)

        for d in self._directories:
            # try:
                topic = Topic(self, d)
                topic.load_documents()
                name = topic.name
                self._topics[name] = topic
            # except:
            #     pass
        pass
    pass

    def save_dictionary(self, filepath="topics_dict.txt"):
        self._corpus_dict.save_as_text(filepath)
    pass

    def load_dictionary(self, filepath="topics_dict"):
        self._corpus_dict.load_from_text(filepath)
    pass

    # -----------------------------------------------------------------------
    # Dimension reduction - LDA
    # -----------------------------------------------------------------------

    def extract_topics(self, topics=None):
        if topics is None:
            topics = self.topics
        if type(topics) == str:
            topics = [topics]

        for name in topics:
            topic = self._topics[name]
            topic.extract_topics()
        pass
    pass

    def save_topics(self, topics=None):
        if topics is None:
            topics = self.topics
        if type(topics) == str:
            topics = [topics]
        for name in topics:
            topic = self._topics[name]
            topic.save_topics()
        pass
    pass

    def load_topics(self, topics=None):
        if topics is None:
            topics = self.topics
        if type(topics) == str:
            topics = [topics]
        for name in topics:
            topic = self._topics[name]
            topic.load_topics()
        pass
    pass

    # -----------------------------------------------------------------------
    # Implementation
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

    def text_to_bow(self, text):
        """
        Convert the text in a bag of words
        :param str text: text to parse
        :return list[(int,int)]: bag of words
        """
        words = self.text_to_words(text)
        bow = self.doc2bow(words, False)
        return bow
    pass

    def doc2bow(self, words, allow_update=False):
        return self._corpus_dict.doc2bow(words, allow_update=allow_update)
    pass

    # -----------------------------------------------------------------------
    # Implementation
    # -----------------------------------------------------------------------

    def _normalize(self, w):
        w = w.lower()
        w = self._stemr.normalize(w)
        return w
    # end

    #
    # check if the word is valid
    #
    def _valid(self, w):
        if len(w) < self._mlen:
            return False
        if self._stopw.is_sw(w):
            return False
        return True
    # end

    # -----------------------------------------------------------------------
    # End
    # -----------------------------------------------------------------------
# end


# ===========================================================================
#
# ===========================================================================
