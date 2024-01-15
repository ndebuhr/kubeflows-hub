import kfp.dsl as dsl

from kfp import compiler
from kfp.dsl import Artifact, Input, Output
from typing import Dict, List


@dsl.component(
    base_image="pytorch/pytorch:2.0.1-cuda11.7-cudnn8-runtime",
    packages_to_install=[
        "transformers",
        "torch",
        "accelerate",
        "Pillow",
        "appengine-python-standard",
    ],
)
def generate_caption_blip2(
    image: Input[Artifact],
    caption: Output[Artifact],
    model: str = "Salesforce/blip2-opt-2.7b",
):
    import torch

    from PIL import Image
    from transformers import Blip2Processor, Blip2ForConditionalGeneration

    device = "cuda" if torch.cuda.is_available() else "cpu"
    processor = Blip2Processor.from_pretrained(model)
    model = Blip2ForConditionalGeneration.from_pretrained(
        model, torch_dtype=torch.float16
    )
    model.to(device)

    image_file = Image.open(image.path)

    inputs = processor(images=image_file, return_tensors="pt").to(device, torch.float16)

    generated_ids = model.generate(**inputs)
    generated_text = processor.batch_decode(generated_ids, skip_special_tokens=True)
    generated_text = generated_text[0].strip()

    with open(caption.path, "w") as file:
        file.write(generated_text)
    caption.metadata["mimeType"] = "text/plain"


@dsl.component(
    base_image="python:3.11",
    packages_to_install=["google-cloud-aiplatform"],
)
def generate_text_embeddings_google(
    text_filepaths: List[str],
    embeddings: Output[Artifact],
    model: str = "textembedding-gecko@001",
    restricts: List[Dict] = None,
):
    import json
    import os
    from vertexai.preview.language_models import TextEmbeddingModel

    model = TextEmbeddingModel.from_pretrained(model)

    # Batch into groups of 5, because that's the maximum batch size for the model
    for i in range(0, len(text_filepaths), 5):
        batch = []
        for text_filepath in text_filepaths[i : i + 5]:
            with open(text_filepath, "r") as file:
                text = file.read()
                batch.append(text)
        embedding_results = model.get_embeddings(batch)
        for text_filepath, embedding_result in zip(
            text_filepaths[i : i + 5], embedding_results
        ):
            with open(embeddings.path, "w") as file:
                # The format here is deliberately in alignment with the Vertex AI Vector Search service
                data = {
                    "id": text_filepath,
                    "embedding": embedding_result.values,
                }
                if restricts:
                    data["restricts"] = restricts
                json.dump(data + "\n", file)

    nearest_neighbors.metadata["mimeType"] = "application/jsonl"


@dsl.component(
    base_image="python:3.11", packages_to_install=["google-auth", "requests"]
)
def generate_image_embeddings_google(
    image_filepaths: List[str],
    embeddings: Output[Artifact],
    api_location: str = "us-central1",
    api_rps: int = 2,  # for rate limiting
    model: str = "multimodalembedding@001",
    restricts: List[Dict] = None,
):
    import base64
    import google.auth
    import google.auth.transport.requests
    import json
    import requests
    import time

    creds, project = google.auth.default()
    project_id = project.split(":")[1]

    auth_req = google.auth.transport.requests.Request()
    creds.refresh(auth_req)

    for image_filepath in image_filepaths:
        with open(image_filepath, "rb") as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode("utf-8")
            response = requests.post(
                f"https://{location}-aiplatform.googleapis.com/v1/projects/{project_id}/locations/{location}/publishers/google/models/{model}:predict",
                headers={"Authorization": f"Bearer {creds.token}"},
                json={"instances": [{"image": {"bytesBase64Encoded": encoded_image}}]},
            )
            # Sleep to avoid rate limiting
            time.sleep(1 / api_rps)
            if response.status_code != 200:
                raise Exception(f"Error: {response.status_code}")
            else:
                embedding = {
                    "id": image_filepath,
                    "embedding": response.json()["predictions"][0]["imageEmbedding"],
                }
                if restricts:
                    embedding["restricts"] = restricts
                with open(embeddings.path, "w") as f:
                    json.dump(embeddings_data + "\n", f)

    embeddings.metadata["mimeType"] = "application/jsonl"


@dsl.component(base_image="python:3.11", packages_to_install=["openai"])
def generate_llm_response_openai(
    prompt: Input[Artifact],
    response: Output[Artifact],
    openai_api_key: str,
    model: str = "gpt-4",
):
    import json
    import tiktoken
    from openai import OpenAI

    client = OpenAI(api_key=openai_api_key)

    with open(prompt.path, "r") as file:
        content = file.read()

    completion = client.chat.completions.create(
        model=model, messages=[{"role": "user", "content": content}]
    )

    with open(response.path, "w") as file:
        file.write(completion.choices[0].message.content)

    embeddings.metadata["mimeType"] = "text/plain"


compiler.Compiler().compile(generate_caption_blip2, "generate-caption-blip2.yaml")
compiler.Compiler().compile(
    generate_text_embeddings_google, "generate-text-embeddings-google.yaml"
)
compiler.Compiler().compile(
    generate_llm_response_openai, "generate-llm-response-openai.yaml"
)
