import kfp.dsl as dsl

from kfp import compiler
from kfp.dsl import Artifact, Output


@dsl.component(
    base_image="python:3.11", packages_to_install=["requests", "BeautifulSoup4"]
)
def scrape_website_text(
    website_uri: str,
    html: Output[Artifact],
):
    import requests
    from bs4 import BeautifulSoup

    response = requests.get(webpage_uri)

    if response.status_code == 200:
        webpage = response.text
        soup = BeautifulSoup(webpage, "html.parser")
        text = soup.get_text()
    else:
        raise Exception(f"Failed to scrape {webpage_uri}.")

    with open(html.path, "w") as file:
        file.write(text)

    html.metadata["mimeType"] = "text/html"


compiler.Compiler().compile(scrape_website_text, "scrape-website-text.yaml")
