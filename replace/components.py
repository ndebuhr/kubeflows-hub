import kfp.dsl as dsl

from kfp import compiler
from kfp.dsl import Artifact, Input, Output


@dsl.component(base_image="python:3.11", packages_to_install=["moviepy"])
def replace_audio_in_video(
    video_input: Input[Artifact],
    audio_input: Input[Artifact],
    video_output: Output[Artifact],
    video_codec: str = "libx264",
    audio_codec: str = "aac",
    mime_type: str = "video/mp4",
):
    from moviepy.editor import AudioFileClip, VideoFileClip

    # Load the new audio file
    audio = AudioFileClip(audio_input.path)

    # Load the video file
    video = VideoFileClip(video_input.path)

    # Replace the audio on the video
    video = video.set_audio(audio)

    # Export the video file
    video.write_videofile(
        video_output.path,
        codec=video_codec,
        audio_codec=audio_codec,
        temp_audiofile="temp-audio.m4a",
        remove_temp=True,
    )

    combined_video.metadata["mimeType"] = mime_type


compiler.Compiler().compile(replace_audio_in_video, "replace-audio-in-video.yaml")
