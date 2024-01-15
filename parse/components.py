import kfp.dsl as dsl

from kfp import compiler
from kfp.dsl import Artifact, Input, Output
from typing import List


@dsl.component(
    base_image="python:3.11", packages_to_install=["google-cloud-documentai"]
)
def parse_pdf_google(
    pdf: Input[Artifact],
    text: Output[Artifact],
    documentai_project_id: str,
    documentai_processor_id: str,
    documentai_location: str = "us",
):
    from google.cloud import documentai
    from google.api_core.client_options import ClientOptions

    MIME_TYPE = "application/pdf"

    opts = ClientOptions(
        api_endpoint=f"{documentai_location}-documentai.googleapis.com"
    )
    client = documentai.DocumentProcessorServiceClient(client_options=opts)
    name = client.processor_path(
        documentai_project_id, documentai_location, documentai_processor_id
    )

    with open(pdf.path, "rb") as file:
        content = file.read()

    raw_document = documentai.RawDocument(content=content, mime_type=MIME_TYPE)
    request = documentai.ProcessRequest(name=name, raw_document=raw_document)
    result = client.process_document(request=request)
    document = result.document

    with open(text.path, "w") as file:
        file.write(document.text)
    text.metadata["mimeType"] = "text/plain"


compiler.Compiler().compile(parse_pdf_google, "parse-pdf-google.yaml")
