from path import Path
from pprint import pprint
import re as rexp
import numpy as np
import snowballstemmer as sbs
import gensim.corpora as corpora
import gensim.models as models
import gensim.similarities as similarities
import gensim.models.basemodel as basemodel


def save_list(lines, file):
    with open(file, mode="w") as f:
        for l in lines:
            f.write(l + "\n")
        f.close()
    pass
pass

def load_list(file):
    with open(file, mode="r") as f:
        lines = [l.strip() for l in f]
        f.close()
    pass
    return lines
pass

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

class NullModel(basemodel.BaseTopicModel):

    def __init__(self, corpus, id2word=None):
        super().__init__()
        self._corpus = corpus
        self._id2word = id2word
    pass

    def __getitem__(self, bow, eps=None):
        return bow

    def save(self, filepath):
        corpora.MmCorpus.serialize(filepath, self._corpus)
        self._id2word.save_as_text(filepath + ".id2w")

    @classmethod
    def load(cls, filepath):
        corpus = corpora.MmCorpus(filepath)
        id2word = corpora.Dictionary.load_from_text(filepath + ".id2w")
        return NullModel(corpus, id2word)

    def print_topics(self):
        return "NullModel has no topics"

pass

# ===========================================================================
#
# ===========================================================================

class TopicHandler:

    # -----------------------------------------------------------------------
    # Constructor
    # -----------------------------------------------------------------------

    def __init__(self, topics, model_type="lda", num_topics=100):
        """

        :param Topics topics:
        :param Path root:
        """
        self._topics = topics
        """:type: Topics"""

        self._model_type = model_type
        """:type: str"""

        self._num_topics=num_topics
        """:type: int"""

        self._corpus = None
        """:type: list[list[]]"""

        self._file_names = None
        """:type: list[str]"""

        self._wdict = corpora.Dictionary()
        """:type: corpora.Dictionary"""

        self._topic_model = None
        """:type: basemodel.BaseTopicModel"""

        self._index = None
        """:type: similarities.MatrixSimilarity"""

        self._name = "TopicHandler"
        """:type: str"""
    pass

    # -----------------------------------------------------------------------
    # Properties
    # -----------------------------------------------------------------------

    @property
    def topic_names(self):
        return self._topic_names

    # -----------------------------------------------------------------------
    # load_documents
    # -----------------------------------------------------------------------

    def compose_corpus(self, directory):
        """
        
        :param str|list[str] directory: directories with the documents 
        """

        dirs = self._scan_dirs(directory)

        self._corpus = []
        self._topic_names = []
        self._file_names = []
        self._load_documents(dirs)
        self._create_models()
    pass

    def _scan_dirs(self, directory):
        if type(directory) == str:
            dirs = [directory]
        else:
            dirs = directory

        subdirs = []
        for adir in dirs:
            subdirs.extend(Path(adir).dirs())

        return subdirs
    # end

    # def _load_documents(self):
    #     print("[%s] Compose corpus ..." % self._name)
    #
    #     topics = self._topics
    #     for pattern in topics._patterns:
    #         for file in self._root.files(pattern=pattern):
    #             bow = self._load_file(file, allow_update=True)
    #             self._filenames.append(str(file.name))
    #             self._corpus.append(bow)
    #         pass
    #     pass
    # pass

    def _load_documents(self, dirs):
        for adir in dirs:
            root = Path(adir)
            topic_name = str(root.name)
            print(topic_name)
            for pattern in self._topics._patterns:
                for file in root.files(pattern=pattern):
                    bow = self._load_file(file, allow_update=True)
                    self._corpus.append(bow)
                    self._file_names.append(str(file.name))
                    self._topic_names.append(topic_name)
                pass
            pass
        pass
    pass

    def _create_models(self):
        print("Create models ...")

        if self._model_type == "lda":
            self._topic_model = models.LdaModel(self._corpus, id2word=self._wdict, num_topics=self._num_topics)
        elif self._model_type == "lsi":
            self._topic_model = models.LsiModel(self._corpus, id2word=self._wdict, num_topics=self._num_topics)
        elif self._model_type == "hdp":
            self._topic_model = models.HdpModel(self._corpus, id2word=self._wdict)
        elif self._model_type == "none":
            self._topic_model = NullModel(self._corpus, id2word=self._wdict)
        else:
            raise SyntaxError("Invalid model_type '%s'" % self._model_type)

        self._index = similarities.MatrixSimilarity(self._topic_model[self._corpus])
    pass

    def save_corpus(self, directory=None):
        print("[%s] Save corpus ..." % self._name)

        dir = "%s/" % (directory if directory else ".")
        name = self._name
        ext = self._model_type

        self._topic_model.save(dir + name + "." + ext)
        self._wdict.save_as_text(dir + name + ".dict")
        corpora.BleiCorpus.serialize(dir + name + ".blei", self._corpus)
        self._index.save(dir + name + ".index")
        save_list(self._file_names, dir + name + ".file_names")
        save_list(self._topic_names, dir + name + ".topic_names")
    pass

    def load_corpus(self, directory=None):
        print("[%s] Load corpus ..." % self._name)
        name = self._name
        ext  = self._model_type
        dir = "%s/" % (directory if directory else ".")

        self._wdict = corpora.Dictionary.load_from_text(dir + name + ".dict")

        if self._model_type == "lda":
            self._topic_model = models.LdaModel.load(dir + name + "." + ext)
        elif self._model_type == "lsi":
            self._topic_model = models.LsiModel.load(dir + name + "." + ext)
        elif self._model_type == "hdp":
            self._topic_model = models.HdpModel.load(dir + name + "." + ext)
        else:
            self._topic_model = NullModel.load(dir + name + "." + ext)

        self._corpus = corpora.BleiCorpus(self._corpus, dir + name + ".blei")
        self._index = similarities.MatrixSimilarity.load(dir + name + ".index")
        self._file_names = load_list(dir + name + ".file_names")
        self._topic_names = load_list(dir + name + ".topic_names")
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
        return self._wdict.doc2bow(words, allow_update=allow_update)
    pass

    def _has_word(self, w):
        return w in self._wdict.token2id
    pass

    # -----------------------------------------------------------------------
    # topic_for_bow
    # -----------------------------------------------------------------------

    # def topic_for_words(self, words):
    #     """
    #     Convert the list of words in a 'bow'
    #
    #     :param list[str] words: list of words
    #     :return list[tuple]: 'bow'
    #     """
    #     print("[%s] Compare with documents ..." % self._name)
    #
    #     bow = self._doc2bow(words)
    #     topics = self._topic_model[bow]
    #
    #     return topics
    # pass

    def missing_words(self, words):
        """
        Check the words not presents in the dictionary
        
        :param list[str] words: 
        :return list[str]: unknown words 
        """
        missing = set(w for w in words if w not in self._wdict.token2id)
        return list(missing)
    pass

    def query(self, words, min_score=0.0):
        """
        
        :param list[str] words: 
        :param float min_score: minimum valid score 
        :return dict[str, float]: topic scores 
        """
        bow = self._doc2bow(words)
        topics = self._topic_model[bow]

        scores = list(self._index[topics])

        dtopics = dict()
        for i in range(len(scores)):
            score = scores[i]
            stopic = self._topic_names[i]

            if score > min_score:
                if stopic not in dtopics:
                    dtopics[stopic] = 0.0
                dtopics[stopic] += score
            pass
        pass
        ltopics = [(k,dtopics[k]) for k in dtopics]
        ltopics = sorted(ltopics, key=lambda t: t[1], reverse=True)
        return ltopics if len(ltopics) > 0 else [("Unknown", 0.0)]
    pass

    def compare(self, words1, words2):
        bow1 = self._doc2bow(words1)
        topics1 = self._topic_model[bow1]
        score1 = self._index[topics1]
        mod1 = 1.#np.linalg.norm(score1)
        if mod1 == 0: mod1 = 1

        bow2 = self._doc2bow(words2)
        topics2 = self._topic_model[bow2]
        score2 = self._index[topics2]
        mod2 = 1.#np.linalg.norm(score2)
        if mod2 == 0: mod2 = 1

        # print(score1)
        # print(score2)
        return np.dot(score1/mod1, score2/mod2)

    # -----------------------------------------------------------------------
    # Dump
    # -----------------------------------------------------------------------

    def dump(self):
        print("[%s]" % self._name)
        print("... %s" % self._model_type)
        print("... %s" % self._topic_names)
        pprint(self._topic_model.print_topics())
        print("")
    pass

    # -----------------------------------------------------------------------
    # End
    # -----------------------------------------------------------------------
pass


class Topics:

    # -----------------------------------------------------------------------
    # Constructor
    # -----------------------------------------------------------------------

    def __init__(self, pattern="*.txt",
                 re="[^A-Za-zàáèéìíòóùú]",
                 stopwords=None, stemrules=None, minlen=1,
                 model_type="lda", num_topics=100):
        """
        Initialize the Topics manager
        :param str|list[str] pattern: list of file patterns to select
        :param str re: regular expression used to split the file
        :param str stopwords: file with the list of stopwords
        :param str stemrules: file with stem rules
        :param int minlen: minimum length of the words
        :param str model_type: topic model. One of "lda", "lsi" hdp"
        :param int num_topics: number of topics
        """

        if type(pattern) != list:
            pattern = [pattern]

        self._patterns = pattern
        """:type: list[str]"""

        self._re = re
        """:type: str"""

        self._mlen = minlen
        """:type: int"""

        self._num_topics = num_topics
        """:type: int"""

        self._model_type = model_type
        """:type: str"""

        self._topic_handler = None
        """:type: TopicHandler"""

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
        self._topic_handler = TopicHandler(self,
            model_type=self._model_type,
            num_topics=self._num_topics)
    pass

    # -----------------------------------------------------------------------
    # Properties
    # -----------------------------------------------------------------------

    @property
    def topic_names(self):
        """
        List of defined topics

        :return iter[str]:
        """
        return self._topic_handler.topic_names
    pass

    # -----------------------------------------------------------------------
    # Corpora
    # -----------------------------------------------------------------------

    def compose_corpora(self, directory):
        """
        Load the documents in the directories specified by topics
        """
        # load the documents in each topic and create the dictionary
        self._topic_handler.compose_corpus(directory)
    pass

    def save_corpora(self, directory=None):
        """
        Save corpora for each topic
        """
        print("Save corpora ...")

        self._check_directory(directory)

        self._topic_handler.save_corpus(directory=directory)
    pass

    def load_corpora(self, directory=None):
        """
        Load the corpora related to each topic
        """
        print("Load corpora ...")

        self._topic_handler.load_corpus(directory=directory)
    pass

    def _check_directory(self, directory):
        if not directory:
            return

        d = Path(directory)
        if not d.exists():
            d.mkdir_p()
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
    # Query
    # -----------------------------------------------------------------------

    def missing_words(self, text):
        words = self.text_to_words(text)
        return self._topic_handler.missing_words(words)
    pass

    def query(self, text, min_score=0):
        """
        Analyze the query and return the score related to each topic
        
        :param str text: 
        :param float min_score: minimum score
        :return list[(str,float)]: scores for each topic, sorted 
        """
        words = self.text_to_words(text)
        return self._topic_handler.query(words, min_score=min_score)
    pass

    def compare(self, text1, text2):
        words1 = self.text_to_words(text1)
        words2 = self.text_to_words(text2)
        return self._topic_handler.compare(words1, words2)
    pass

    # -----------------------------------------------------------------------
    # Topics selection
    # -----------------------------------------------------------------------

    # def topic_for_text(self, text):
    #     words = self.text_to_words(text)
    #     return self.topic_for_words(words)
    # pass

    # def topic_for_file(self, filepath):
    #     words = self.file_to_words(filepath)
    #     return self.topic_for_words(words)
    # pass

    # def topic_for_words(self, words):
    #     return self._topic_handler.topic_for_words(words)
    # pass

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
    # Implementation
    # -----------------------------------------------------------------------

    def __iter__(self):
        return self._topic_handler.__iter__()
    pass

    # -----------------------------------------------------------------------
    # Dump
    # -----------------------------------------------------------------------

    def dump(self):
        self._topic_handler.dump()
    pass

    # -----------------------------------------------------------------------
    # End
    # -----------------------------------------------------------------------
pass


# ===========================================================================
#
# ===========================================================================
