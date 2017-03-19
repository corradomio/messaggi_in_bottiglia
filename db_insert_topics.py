import orientdb as o
import neo4jdb as n
from path import Path
import time


def main(odb):

    _insert_documents(odb)
    _insert_topics(odb)
    _link_document_to_topic(odb)

# end


def _link_document_to_topic(odb):
    odb.create_class("IN_TOPIC", {"extends": "E"})

    docs = odb.select_documents("Document")
    for doc in docs:
        topic_name = doc.topic

        topic = odb.get_document("Topic", where={"topic": topic_name})

        rid = odb.create_edge("IN_TOPIC", doc._rid, topic._rid)
        print(rid)
    # end
# end


def _insert_topics(odb):
    odb.create_class("Topic", {"extends": "V", "topic": str})

    topic_root = Path("topics")
    for topic_dir in topic_root.dirs():
        topic_name = str(topic_dir.name)
        print (topic_name)

        if not odb.exists_document("Topic", where={"topic": topic_name}):
            odb.insert_document("Topic", body={"topic": topic_name})
    # end
# end


def _insert_documents(odb):
    odb.create_class("Document", {"extends":"V", "name": str, "topic": str})

    topic_root = Path("topics")
    for topic_dir in topic_root.dirs():
        topic_name = str(topic_dir.name)
        print (topic_name)
        for doc_file in topic_dir.files(pattern="*.txt"):
            file_name = str(doc_file.name)
            print("... %s" % file_name)

            if not odb.exists_document("Document", where={"name":file_name, "topic":topic_name}):
                odb.insert_document("Document", body={"name":file_name, "topic":topic_name})
        # end
    # end
# end


if __name__ == "__main__":
    # odb = o.OrientDB("orient://root:password@cmshooter.homeip.net:2424/test")
    odb = n.Neo4jDB("bolt://theta:7687")
    odb.open_db()
    main(odb)
    odb.close()
