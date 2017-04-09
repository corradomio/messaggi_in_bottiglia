from pprint import pprint
import topics_class as t


def main():
    # crea l'oggetto da  utilizzare per l'information retrieval

    topics = t.Topics(
        stopwords="stopwords.txt",  # lista di stopword
        stemrules="stemmer.txt",    # lista di regole per lo stemmer
        num_topics=100,             # numero di topic da utilizzare
        model_type="lda"            # TopiC Model da utilizzare: 'lda', 'lsi', 'hdp', 'none'
    )

    # legge l'addetramento dalla directory indicata
    topics.load_corpora(directory="models")

    q1 = "che cosa e' il teorema di Pitagora"
    q2 = "come funziona il teorema di Euclide"
    q3 = "ma il teorema di Pitagora e' proprio questo qui'"

    s12 = topics.compare_query(q1, q2)
    s13 = topics.compare_query(q1, q3)
    s23 = topics.compare_query(q2, q3)

    pprint({q1+" ~ "+q2:s12,
           q1+" ~ "+q3:s13,
           q2+" ~ "+q3:s23})

    scores = topics.topics_query("Qualcuno mi può spiegare le equazioni parametriche con la formula di waring ?? Fra 4 giorni abbiamo la verifica e non l'ho capita")
    print(scores)
pass


if __name__ == "__main__":
    main()