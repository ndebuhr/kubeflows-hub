import kfp.dsl as dsl

from kfp import compiler
from kfp.dsl import Artifact, Input, Output


@dsl.component(
    base_image="python:3.11", packages_to_install=["google-cloud-aiplatform"]
)
def count_tokens_google(
    text: Input[Artifact],
    token_count: Output[Artifact],
    model_name: str = "gemini-pro",
) -> int:
    import vertexai
    from vertexai.preview.generative_models import GenerativeModel

    vertexai.init()

    model = GenerativeModel(model_name)

    with open(text.path, "r") as file:
        text = file.read()
        token_count = model.count_tokens(text)

    with open(token_count.path, "w") as file:
        file.write(token_count)

    token_count.metadata["mimeType"] = "text/plain"

    return token_count


@dsl.component(base_image="python:3.11", packages_to_install=["tiktoken"])
def count_tokens_openai(
    text: Input[Artifact],
    token_count: Output[Artifact],
    model_name: str = "gpt-4",
) -> int:
    import tiktoken

    encoding = tiktoken.encoding_for_model(model_name)

    with open(text.path, "r") as file:
        contents = file.read()
        tokens = encoding.encode(contents)
        token_count = str(len(tokens))

    with open(token_count.path, "w") as file:
        file.write(token_count)

    token_count.metadata["mimeType"] = "text/plain"

    return token_count


compiler.Compiler().compile(count_tokens_google, "count-tokens-google.yaml")
compiler.Compiler().compile(count_tokens_openai, "count-tokens-openai.yaml")
