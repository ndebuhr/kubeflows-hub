import kfp.dsl as dsl

from kfp import compiler
from kfp.dsl import Artifact, Input, Output
from typing import List


@dsl.component(base_image="python:3.11", packages_to_install=["opencv-python-headless"])
def extract_video_frames(
    video: Input[Artifact],
    frame_filepath_template: str = "/tmp/frame-%d.png",
    frame_sampling: int = 1,  # extract every nth frame
    frame_offset: int = 0,  # set an offset for the first extraction
) -> List[str]:
    import cv2

    cap = cv2.VideoCapture(video.path)
    fps = cap.get(cv2.CAP_PROP_FPS)

    if not cap.isOpened():
        raise Exception(f"Could not open video: {video.uri}")

    frames = []
    for i in range(
        frame_offset, int(cap.get(cv2.CAP_PROP_FRAME_COUNT)), frame_sampling
    ):
        cap.set(cv2.CAP_PROP_POS_FRAMES, i)
        ret, frame = cap.read()

        if ret:
            cv2.imwrite(frame_filepath_template % i, frame)
            frames.append(frame_filepath_template % i)
        else:
            raise Excaption(f"Could not read frame: {i}")

    cap.release()

    return frames


@dsl.component(
    base_image="python:3.11", packages_to_install=["google-cloud-videointelligence"]
)
def extract_video_intelligence(
    video: Input[Artifact],
    objects: Output[Artifact],
    timeout: int = 7200,
    features: List[str] = ["TEXT_DETECTION"],
):
    from google.cloud import videointelligence

    video_client = videointelligence.VideoIntelligenceServiceClient()

    features = []
    if "OBJECT_TRACKING" in features:
        features.append(videointelligence.Feature.OBJECT_TRACKING)
    if "SHOT_CHANGE_DETECTION":
        features.append(videointelligence.Feature.SHOT_CHANGE_DETECTION)
    if "TEXT_DETECTION":
        features.append(videointelligence.Feature.TEXT_DETECTION)
    if "LABEL_DETECTION":
        features.append(videointelligence.Feature.LABEL_DETECTION)
    if "EXPLICIT_CONTENT_DETECTION":
        features.append(videointelligence.Feature.EXPLICIT_CONTENT_DETECTION)

    operation = video_client.annotate_video(
        request={
            "features": features,
            "input_uri": video.uri,
        }
    )

    result = operation.result(timeout=timeout)

    object_annotations = result.annotation_results[0].object_annotations

    with open(objects.path, "w") as f:
        json.dump(object_annotations, f)
    objects.metadata["mimeType"] = "application/json"


@dsl.component(base_image="python:3.11", packages_to_install=["av"])
def extract_video_metadata(
    video: Input[Artifact],
    metadata: Output[Artifact],
):
    import av

    container = av.open(video.path)

    video_stream = next(s for s in container.streams if s.type == "video")

    with open(metadata.path, "w") as f:
        json.dump(video_stream, f)
    metadata.metadata["mimeType"] = "application/json"


compiler.Compiler().compile(extract_video_frames, "extract-video-frames.yaml")
compiler.Compiler().compile(
    extract_video_intelligence, "extract-video-intelligence.yaml"
)
compiler.Compiler().compile(extract_video_metadata, "extract-video-metadata.yaml")
