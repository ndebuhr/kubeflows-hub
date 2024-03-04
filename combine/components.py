import kfp.dsl as dsl

from kfp import compiler
from kfp.dsl import Artifact, Input, Output
from typing import List


@dsl.component(base_image="python:3.11", packages_to_install=["moviepy"])
def combine_video_parts(
    unsplit_video: Input[Artifact],
    part_filepaths: List[str],
    combined_video: Output[Artifact],
    video_codec: str = "libx264",
    audio_codec: str = "aac",
    mime_type: str = "video/mp4",
):
    from moviepy.editor import VideoFileClip, concatenate_videoclips

    # Load the original video file
    original_video = VideoFileClip(unsplit_video.path)

    # Load the video parts
    video_parts = [VideoFileClip(part) for part in part_filepaths]

    # Concatenate the video parts
    final_video = concatenate_videoclips(video_parts)

    # Use the audio from the original file
    final_video = final_video.set_audio(original_video.audio)

    # Export the final video
    final_video.write_videofile(
        combined_video.path, codec=video_codec, audio_codec=audio_codec
    )

    combined_video.metadata["mimeType"] = mime_type


compiler.Compiler().compile(combine_video_parts, "combine-video-parts.yaml")
