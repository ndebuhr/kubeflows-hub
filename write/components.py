import kfp.dsl as dsl

from kfp import compiler
from kfp.dsl import Artifact, Input
from typing import List


@dsl.component(base_image="python:3.11", packages_to_install=["elasticsearch"])
def write_embeddings_elasticsearch(
    embeddings: Input[Artifact],
    embedding_dimension: int,
    elasticsearch_hosts: List[str],
    elasticsearch_username: str,
    elasticsearch_password: str,
    elasticsearch_index: str,
    create_index: bool = True,
):
    from elasticsearch import Elasticsearch

    es = Elasticsearch(
        hosts=elasticsearch_hosts,
        basic_auth=(elasticsearch_username, elasticsearch_password),
    )

    mapping = {
        "mappings": {
            "properties": {
                "embedding": {"type": "dense_vector", "dims": embedding_dimension}
            }
        }
    }

    if create_index:
        es.indices.create(index=elasticsearch_index, body=mapping)

    with open(embeddings.path, "r") as file:
        for line in file:
            embedding = json.loads(line)
            es.index(
                index=elasticsearch_index,
                id=embedding["id"],
                body={"embedding": embedding["embedding"]},
            )


compiler.Compiler().compile(
    write_embeddings_elasticsearch, "write-embeddings-elasticsearch.yaml"
)
