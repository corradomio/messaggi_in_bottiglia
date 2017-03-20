import topics_class as t


def main():
    topics = t.Topics(root = "topics")
    topics.compose_dictionary()
    topics.save_dictionary()
    pass



if __name__ == "__main__":
    main()
