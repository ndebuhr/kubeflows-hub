import kfp.dsl as dsl

from kfp import compiler
from kfp.dsl import Artifact, Output
from typing import List


@dsl.component(base_image="python:3.11", packages_to_install=["matplotlib"])
def visualize_via_histogram(
    values: List[int],
    histogram: Output[Artifact],
    bins: int = 20,
    title: str = "Histogram",
    xlabel: str = "Value",
    ylabel: str = "Count",
):
    import matplotlib.pyplot as plt

    plt.hist(values, bins=bins)
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)

    plt.savefig(output.path)

    combined_video.metadata["mimeType"] = "image/png"


compiler.Compiler().compile(visualize_via_histogram, "visualize-via-histogram.yaml")
