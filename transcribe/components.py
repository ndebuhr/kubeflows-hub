import kfp.dsl as dsl

from kfp import compiler
from kfp.dsl import Artifact, Input, Output


@dsl.component(base_image="python:3.11", packages_to_install=["google-cloud-speech"])
def transcribe_audio_google(
    audio: Input[Artifact],
    transcript: Output[Artifact],
    audio_channel_count: int = 2,
    sample_rate_hertz: int = 48000,
    language_code: str = "en-US",
    speech_to_text_model: str = "video",
    long_running: bool = True,  # Required for videos longer than a minute
):
    import json
    import os
    import re

    from google.cloud import speech

    client = speech.SpeechClient()

    audio_data = speech.RecognitionAudio(uri=audio.uri)

    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=sample_rate_hertz,
        language_code=language_code,
        audio_channel_count=audio_channel_count,
        model=speech_to_text_model,
    )

    if long_running:
        operation = client.long_running_recognize(config=config, audio=audio_data)
        response = operation.result()
    else:
        response = client.recognize(config=config, audio=audio)

    with open(transcript.path, "w") as file:
        for result in response.results:
            file.write(result.alternatives[0].transcript + "\n")

    transcript.metadata["mimeType"] = "text/plain"


compiler.Compiler().compile(transcribe_audio_google, "transcribe-audio-google.yaml")
