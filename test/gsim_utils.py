from path import Path as path
import re as rexp
import logging
import gensim.corpora as corpora
import snowballstemmer as sbs


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
        self._rules = [None] * (self.N+1)

        self._stemmer = sbs.stemmer('italian')
    # end

    def load_stemrules(self, stfile):
        """
        Load th fie of rules

        :param str stfile:  path of the file to load
        """
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



class FileCorpus:

    # -----------------------------------------------------------------------
    # Constructor
    # -----------------------------------------------------------------------

    def __init__(self, directory=None, pattern=None, file=None,
                 re="[^A-Za-zàáèéìíòóùú]",
                 minlen=1,
                 stopwordfile=None,
                 stemrulesfile=None):
        """
        :param str|list[str] directory: directory to scan
        :param str|list[str] pattern: name-pattern of files to select
        :param str|list[str] file: file(s) path to use. Relative if 'directory' is specified
        :param str re: re used to split the line in tokens
        :param int minlen: minimun length of the words (default: 0)
        :param str stopwordfile: path of the stopword's file to read
        """

        self._files = None
        """:type: list[str]"""
        self._re = re
        """:type: str"""
        self._mlen = minlen
        """:type: int"""
        self._corpus_dict = corpora.Dictionary()
        """:type: corpora.Dictionary"""

        self._stopw = StopWords()
        """:type: StopWords"""
        self._stemr = StemRules()
        """:type: StemRules"""

        self._log = logging.getLogger("FileCorpus")
        """:type: logger.Logger"""

        self._docs = []
        """:type: list[list[str]]"""

        self._compose_file_list(directory, pattern, file)
        self._load_stopwords(stopwordfile)
        self._load_stemrules(stemrulesfile)
    # end

    def _compose_file_list(self, dir, pat, files):
        flist = []

        if isinstance(dir, str):
            dir = [dir]
        if isinstance(pat, str):
            pat = [pat]
        if isinstance(files, str):
            files = [files]

        if dir and pat:
            for d in [path(t) for t in dir]:
                for p in pat:
                    flist = flist + d.files(pattern=p)

        if dir and files:
            for d in [path(t) for t in dir]:
                for f in files:
                    p = d.joinpath(f)
                    if p.exists():
                        flist.append(p)

        self._files = flist
    # end

    def _load_stopwords(self, swfile):
        self._stopw.load_stopwords(swfile)
    # end

    def _load_stemrules(self, srfile):
        self._stemr.load_stemrules(srfile)
    # end

    # -----------------------------------------------------------------------
    # Properties
    # -----------------------------------------------------------------------

    def dictionary(self):
        return self._corpus_dict
    # end

    # -----------------------------------------------------------------------
    # Operations
    # -----------------------------------------------------------------------

    def load_corpus(self):
        """
        Load the specified files as a corpus
        """
        self._log.info("Loading corpus ...")
        corpus = []
        for filepath in self._files:
            self._log.info("... loading '%s' ...", filepath)
            bow = self.load_file(filepath, update=True)
            corpus.append(bow)
        self._log.info("done")
        return corpus
    # end

    def load_file(self, filepath, update=False):
        """
        Load the file and convert it in a bow

        :param str filepath: path of the file to load
        :param bool update: if update the dictionary
        :return list(int,int)]: a bag of words
        """
        doc = []
        with open(filepath, encoding="utf-8", mode="r") as f:
            for text in f:
                words = self.text_to_words(text)
                doc.extend(words)
            pass
            f.close()
        pass
        bow = self._corpus_dict.doc2bow(doc, allow_update=update)
        return bow
    #end

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
    # end

    def text_to_bow(self, text):
        """
        Convert the text in a bag of words
        :param str text: text to parse
        :return list[(int,int)]: bag of words
        """
        words = self.text_to_words(text)
        bow = self._corpus_dict.doc2bow(words, False)
        return bow
    # end

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

    pass

# end


class TopicsCorpus(object):

    def __init__(self, homedirectory, pattern="*.txt"):
        self._home_dir = path(homedirectory)
        self._topic_dirs = self._home_dir.dirs()
        self._topic_dict = dict()
        self._pattern = pattern
    # end

    def load_copuses(self):

        for topicdir in self._topic_dirs:
            name = str(topicdir.name)
            print("Loading topic '%s'" % name)
            fc = FileCorpus(directory=topicdir, pattern=self._pattern)
            fc.load_corpus()
            self._topic_dict[name] = fc
        # end
    # end

    pass

# end
