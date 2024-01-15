import kfp.dsl as dsl

from kfp import compiler
from kfp.dsl import Artifact, Input, Output


@dsl.component(
    base_image="python:3.11",
    packages_to_install=["google-cloud-aiplatform"],
)
def calculate_nearest_neighbors_google(
    embeddings: Input[Artifact],
    nearest_neighbors: Output[Artifact],
    vector_search_index_endpoint_id: str,
    vector_search_deployed_index_id: str,
    nearest_neighbor_count: int = 4,
) -> str:
    import json

    from google.cloud import aiplatform

    similarity_engine = aiplatform.MatchingEngineIndexEndpoint(
        index_endpoint_name=vector_search_index_endpoint_id
    )

    embeddings = []
    with open(embeddings.path, "r") as file:
        for line in file:
            embeddings.append(json.loads(line))

    # Batch into groups of 5
    for i in range(0, len(embeddings), 5):
        batch = [embedding["embedding"] for embedding in embeddings[i : i + 5]]
        responses = similarity_engine.match(
            deployed_index_id=vector_search_deployed_index_id,
            queries=batch,
            num_neighbors=nearest_neighbor_count,
        )

        with open(nearest_neighbors.path, "w") as file:
            for j in range(i, i + 5):
                file.write(
                    json.dumps(
                        {
                            "id": embeddings[i]["id"],
                            "neighbors": [
                                {"id": neighbor.id, "distance": neighbor.distance}
                                for neighbor in responses[j]
                            ],
                        }
                    )
                    + "\n"
                )

    nearest_neighbors.metadata["mimeType"] = "application/jsonl"


compiler.Compiler().compile(
    calculate_nearest_neighbors_google, "calculate-nearest-neighbors-google.yaml"
)
