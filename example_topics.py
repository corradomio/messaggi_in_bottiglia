import topics_class as t


def main():
    # crea l'oggetto da utilizzare per l'information retrieval

    topics = t.Topics(
        stopwords="stopwords.txt",  # lista di stopword
        stemrules="stemmer.txt",    # lista di regole per lo stemmer
        num_topics=100,             # numero di topic da utilizzare
        model_type="lda"            # TopiC Model da utilizzare: 'lda', 'lsi', 'hdp', 'none'
    )

    # addestramento: legge i documenti dalla directory indicata
    # e crea il supporto per il Topic Modelling.
    # deve essere fatto una sola volta
    # topics.compose_corpora(directory="topics")

    # salva l'addestramento nella directory indicata
    # topics.save_corpora(directory="models")

    # legge l'addetramento dalla directory indicata
    topics.load_corpora(directory="models")

    # controlla se la domanda contiene word sconosciute (ad esempio, errori di sintassi)
    mwords = topics.missing_words("Il marcante di Venezia")
    print(mwords)

    mwords = topics.missing_words("Qualcuno mi può spiegare le eqazioni parametriche con la formula di waring ?? Fra 4 giorni abbiamo la verifica e non l'ho capita")
    print(mwords)

    # deduce il topic della domanda
    text = """Ciao a tutti, ho questo testo teatrale di Samuel Beckett e dovrei rispondere al seguente quesito:
    Esamina il comportamento dell'uomo all'inizio della vicenda e il suo atteggiamento alla fine mentre all'inizio egli reagisce agli stimoli mediante azioni concrete, alla fine si mostra deciso a non compiere più alcuna azione.
    Quali sono i motivi di questa trasformazione? Quale nuova convinzione sembra che egli abbia acquisito? Attraverso la rappresentazione di questa trasformazione, quale messaggio ritieni che l'autore intenda trasmettere? Esponi in un testo scritto le tue considerazioni e riflessioni in merito a questi interrogativi.
    Vi allego le foto del testo, grazie mille in anticipo :hi"""
    scores = topics.query(text)
    print(scores)

    scores = topics.query("Qualcuno mi può spiegare le equazioni parametriche con la formula di waring ?? Fra 4 giorni abbiamo la verifica e non l'ho capita")
    print(scores)

    scores = topics.query("Cristo, Maometto, Satana, non esistono?")
    print(scores)
pass




if __name__ == "__main__":
    main()
