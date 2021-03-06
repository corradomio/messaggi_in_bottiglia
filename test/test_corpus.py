import logging
from pprint import pprint

import gensim.models as models

from test.gsim_utils import *

logging.basicConfig(level=0, format="%(levelname)s:%(message)s")


fc = FileCorpus(#directory="topics"],
                # directory=["topics/Chimica"],
                # directory=["topics/ElettrotecnicaEdElettronica"],
                # directory=["topics/Italiano"],
                # directory=["topics/Matematica"],
                # directory=["topics/SistemiAutomatici"],
                directory=["topics/Storia"],
                # directory=[r"D:\RemoteSpace\Books.Other\Lingua Italiana\Dizionari"],
                pattern="*.txt",
                minlen=3,
                stopwordfile="stopwords.txt",
                stemrulesfile="stemmer.txt")

corpus = fc.load_corpus()

dictionary = fc.dictionary()
pprint(dictionary.token2id)

bow = fc.text_to_bow("La rivoluzione Americana e Napoleone")

# tfidf = models.TfidfModel(corpus, id2word=dictionary)
# pprint(tfidf[bow])

lda = models.LdaModel(corpus, id2word=dictionary, num_topics=2)
pprint(lda.show_topics(num_topics=100,num_words=100))

pprint(lda[bow])

# hdp = models.HdpModel(corpus, id2word=dictionary)
# pprint(hdp)

# tc = TopicsCorpus(homedirectory="topics")
# tc.load_copuses()

pass