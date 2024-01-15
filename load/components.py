import kfp.dsl as dsl

from kfp import compiler
from kfp.dsl import Input, Artifact


@dsl.component(
    base_image="python:3.11",
    packages_to_install=["google-cloud-bigquery", "pandas", "pyarrow"],
)
def load_json_into_bigquery(
    data: Input[Artifact],
    dataset_id: str,
    table_id: str,
    orient: str = "records",
):
    import json
    import pandas as pd
    from google.cloud import bigquery

    client = bigquery.Client()

    df = pd.read_json(data.path, orient=orient)

    dataset_ref = client.dataset(dataset_id)
    table_ref = dataset_ref.table(table_id)

    if not df.empty:
        job = client.load_table_from_dataframe(df, table_ref)
        job.result()


compiler.Compiler().compile(load_json_into_bigquery, "load-json-into-bigquery.yaml")
