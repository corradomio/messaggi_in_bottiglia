from pprint import pprint
import gensim.corpora as corpora
import gensim.models as models
import gensim.similarities as similarities
import fileio as fio


def main():

    dir = "models/"
    name = "all"

    file = "topics/Italiano/Myricae - Giovanni Pascoli.txt"

    # legge il dizionario

    print("load dict")
    wdict = corpora.Dictionary.load_from_text("models/all.dict")
    print(wdict)

    # print("load body")
    # body = fio.text_from_file("topics_1/SistemiAutomatici/SistemiAutomatici.txt")
    # pprint(body)


    # print("load doc")
    # bow = fio.words_from_file(file, corpus=False, word2id=wdict)
    # pprint(bow)

    print("compose corpus")
    corpus = fio.words_from_directory([
        "topics/Matematica",
        "topics/ElettrotecnicaEdElettronica",
        "topics/Italiano"
    ], pattern="*.txt", word2id=wdict)
    # pprint(corpus)
    pprint(len(corpus))
    pprint(fio.count_corpus_words(corpus, words=False))
    pprint(fio.count_corpus_words(corpus, words=True))

    print("create similarities")
    index = similarities.MatrixSimilarity(corpus)

    print("compose query")
    query_bow = fio.words_from_text("Che cosa e' un condensatore", word2id=wdict)
    pprint(query_bow)

    print("do the query")
    q = list(index[query_bow])
    pprint(q)
    pprint(len(q))



    print("create lda")
    lda = models.LdaMulticore(corpus, num_topics=10, id2word=wdict, workers=8)

    print("convert corpus in lda")
    corpus_lda = lda[corpus]

    print("convert query in lda")
    query_lda = lda[query_bow]

    print("create similarities lda")
    index_lda = similarities.MatrixSimilarity(corpus_lda)

    print("do the query lda")
    q = list(index_lda[query_lda])
    pprint(q)
    pprint(len(q))


pass

if __name__ == "__main__":
    main()
