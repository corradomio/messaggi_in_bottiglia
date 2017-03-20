from pprint import pprint
import topics_class as t


def main():
    topics = t.Topics(
        root="../topics",
        stopwords="../stopwords.txt",
        stemrules="../stemmer.txt"
    )

    topics.compose_corpora()
    topics.save_corpora("../models")
    topics.load_corpora("../models")

    select = topics.topic_for_text("Mi spiegate le equazioni parametriche con la formula di waring?")

    pprint(select)
pass


if __name__ == "__main__":
    main()
