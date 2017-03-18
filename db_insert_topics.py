import orientdb as o
from path import Path
import time

def main():
    odb = o.OrientDB("orient://root:password@cmshooter.homeip.net:2424/test")
    odb.open_db()

    # _insert_documents(odb)
    # _insert_topics(odb)
    _link_document_to_topic(odb)

    odb.close()
# end

def _my_callback(for_every_record):
    print(for_every_record)

def _link_document_to_topic(odb):
    odb.create_class("IN_TOPIC", {"extends": "E"})

    docs = odb.select_documents("Document")
    for doc in docs:
        topic_name = doc.topic

        topic = odb.get_document("Topic", where={"topic": topic_name})

        rid = odb.create_edge("IN_TOPIC", doc._rid, topic._rid)
        print(rid)



        print(doc.topic)


def _insert_topics(odb):
    odb.create_class("Topic", {"extends": "V", "topic": str})

    topic_root = Path("topics")
    for topic_dir in topic_root.dirs():
        topic = str(topic_dir.name)
        print (topic)

        if not odb.exists_document("Topic", where={"topic": topic}):
            odb.insert_document("Topic", body={"topic": topic})
    # end
# end


def _insert_documents(odb):
    odb.create_class("Document", {"extends":"V", "name": str, "topic": str})

    topic_root = Path("topics")
    for topic_dir in topic_root.dirs():
        topic = str(topic_dir.name)
        print (topic)
        for doc_file in topic_dir.files(pattern="*.txt"):
            file_name = str(doc_file.name)
            print("... %s" % file_name)

            if not odb.exists_document("Document", where={"name":file_name, "topic":topic}):
                odb.insert_document("Document", body={"name":file_name, "topic":topic})
        # end
    # end
# end


if __name__ == "__main__":
    main()