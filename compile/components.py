import kfp.dsl as dsl

from kfp import compiler
from kfp.dsl import Artifact, Output
from typing import List


@dsl.component(
    base_image="python:3.11",
    packages_to_install=["google-cloud-aiplatform"],
)
def compile_batch_job_google(
    input_filepaths: List[str],
    input_mime_type: str,
    batch_data: Output[Artifact],
) -> str:
    with open(batch_data.path, "w") as file:
        for input_filepath in input_filepaths:
            file.write(
                json.dumps(
                    {
                        "content": input_filepath,
                        "mimeType": input_mime_type,
                    }
                )
                + "\n"
            )

    batch_data.metadata["mimeType"] = "application/jsonl"


compiler.Compiler().compile(compile_batch_job_google, "compile-batch-job-google.yaml")
