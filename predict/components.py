import kfp.dsl as dsl

from kfp import compiler
from kfp.dsl import Artifact, Input


@dsl.component(
    base_image="python:3.11",
    packages_to_install=["google-cloud-aiplatform"],
)
def predict_batch_google(
    batch_data: Input[Artifact],
    gcs_destination_prefix: str,
    model: str,  # projects/PROJECT_NUMBER/locations/REGION/models/MODEL_NUMBER
    job_display_name: str,
) -> str:
    classification_model = aiplatform.Model(model)

    batch_prediction_job = classification_model.batch_predict(
        job_display_name=job_display_name,
        gcs_source=batch_data.uri,
        gcs_destination_prefix=gcs_destination_prefix,
        sync=True,
    )

    batch_prediction_job.wait()

    return batch_prediction_job.output_info.gcs_output_directory


compiler.Compiler().compile(predict_batch_google, "predict-batch-google.yaml")
