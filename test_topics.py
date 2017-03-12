import topics_impl as t



def main():
    s = t.Synonimous()
    s.load_synonimous("topics/Italiano/th_it_IT_v2.txt")
    s.dump()
pass

def main_1():

    topics = t.Topics(
        # root="topics",
        directory="topics/Storia",
        stopwords="stopwords.txt",
        stemrules="stemmer.txt",
        minlen=3)
    topics.load_documents()
    topics.save_dictionary()

    topics.extract_topics()
# end


if __name__ == "__main__":
    main()
