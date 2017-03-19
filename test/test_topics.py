import topics_class as t



# def main_1():
#     s = t.Synonimous()
#     s.load_synonimous("topics/Italiano/th_it_IT_v2.txt")
#     s.dump()
# pass
#
# def main():
#
#     topics = t.Topics(
#         # root="topics",
#         directory="topics/Storia",
#         stopwords="stopwords.txt",
#         stemrules="stemmer.txt",
#         minlen=3)
#     topics.load_documents()
#     topics.save_dictionary()
#
#     topics.extract_topics()
# # end

def main():
    topics = t.Topics(root="../topics")

    # topics.compose_dictionary()
    # topics.save_dictionary("../words_dict.txt")
    # topics.compose_corpora()
    # topics.save_corpora()

    topics.load_dictionary("../words_dict.txt")
    topics.load_corpora("../models")

    select = topics.topic_for_text("Mi spiegate le equazioni parametriche con la formula di waring?")

    print(select)



if __name__ == "__main__":
    main()
