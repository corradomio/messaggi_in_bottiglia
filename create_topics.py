import topics_class as t


def main():
    topics = t.Topics(root="topics")
    topics.load_dictionary()
    topics.load_corpora()
    pass



if __name__ == "__main__":
    main()
