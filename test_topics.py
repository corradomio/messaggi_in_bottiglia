from pprint import pprint
import topics_class as t


def main():
    topics = t.Topics(
        root="topics",
        stopwords="stopwords.txt",
        stemrules="stemmer.txt",
        num_topics=100,
        model_type="none"
    )

    # topics.compose_corpora()
    # topics.save_corpora("models")
    topics.load_corpora("models")
    # topics.dump()

    # mwords = topics.missing_words("Il mercante di venezia")
    # print(mwords)

    # scores = topics.query("Il mercante di venezia")
    # print(scores)

    # mwords = topics.missing_words("Qualcuno mi può spiegare le eqazioni parametriche con la formula di waring ?? Fra 4 giorni abbiamo la verifica e non l'ho capita")
    # print(mwords)

    # print()
    # for tt in topics:
    #     print (tt)
    #
    # select = topics.topic_for_text("Qualcuno mi può spiegare le eqazioni parametriche con la formula di waring ?? Fra 4 giorni abbiamo la verifica e non l'ho capita")
    # pprint(select)
    #
    #
#     text = """Ciao a tutti, ho questo testo teatrale di Samuel Beckett e dovrei rispondere al seguente quesito:
# Esamina il comportamento dell'uomo all'inizio della vicenda e il suo atteggiamento alla fine mentre all'inizio egli reagisce agli stimoli mediante azioni concrete, alla fine si mostra deciso a non compiere più alcuna azione.
# Quali sono i motivi di questa trasformazione? Quale nuova convinzione sembra che egli abbia acquisito? Attraverso la rappresentazione di questa trasformazione, quale messaggio ritieni che l'autore intenda trasmettere? Esponi in un testo scritto le tue considerazioni e riflessioni in merito a questi interrogativi.
# Vi allego le foto del testo, grazie mille in anticipo :hi"""
#     mwords = topics.missing_words(text)
#     pprint(mwords)
#
#     scores = topics.query(text)
#     print(scores)

    # print(topics.compare("Qualcuno mi può spiegare le eqazioni parametriche con la formula di waring ?? Fra 4 giorni abbiamo la verifica e non l'ho capita",
    #                      #"alessandro manzoni"
    #                      "formula di waring"
    #                      ))


pass


if __name__ == "__main__":
    main()
