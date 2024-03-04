import kfp.dsl as dsl

from kfp import compiler
from kfp.dsl import Artifact, Input
from typing import List


@dsl.component(base_image="ndebuhr/python-ffmpeg:3.11", packages_to_install=["pydub"])
def split_audio_on_silence(
    audio: Input[Artifact],
    silence_duration_ms: int,  # in milliseconds
    audio_format: str = "wav",
    absolute_silence_threshold_db: float = None,
    relative_silence_threshold_db: float = -24,
    seek_step_ms: int = 10,  # in milliseconds
    output_filepath_template: str = "/tmp/segment-%d.wav",
) -> List[str]:
    import os
    from pydub import AudioSegment, silence

    if audio_format == "wav":
        audio_data = AudioSegment.from_wav(audio.path)
    elif audio_format == "mp3":
        audio_data = AudioSegment.from_mp3(audio.path)
    else:
        raise ValueError(f"Unsupported audio format: {audio_format}")

    if absolute_silence_threshold_db is not None:
        silence_thresh = absolute_silence_threshold_db
    elif relative_silence_threshold_db is not None:
        silence_thresh = audio_data.dBFS + relative_silence_threshold_db
    else:
        raise ValueError("Must specify either absolute or relative silence threshold")

    silence_segments = silence.detect_silence(
        audio_data,
        min_silence_len=silence_duration,
        silence_thresh=silence_thresh,
        seek_step=seek_step_ms,
    )

    silence_midpoints = [
        int(sum(segment) / len(segment)) for segment in silence_segments
    ]
    audio_split_points = [0] + silence_midpoints + [len(audio_data)]
    audio_segments = list(zip(audio_split_points[:-1], audio_split_points[1:]))

    base_filename = os.path.basename(audio.path)

    output_files = []
    for i, (start, end) in enumerate(audio_segments):
        print(f"Exporting {base_filename} segment {i} from {start} to {end}")
        output_file = output_filepath_template % i
        audio[start:end].export(output_file, format=audio_format)
        output_files.append(output_file)

    return output_files


@dsl.component(base_image="python:3.11", packages_to_install=["pypdf2==2.12.1"])
def split_pdf_by_pages(
    pdf: Input[Artifact],
    output_filepath_template: str = "/tmp/batch-%d.pdf",
    batch_size_pages: int = 1,
) -> List[str]:
    import os
    import PyPDF2

    batch_files = []
    with open(pdf.path, "rb") as file:
        pdf_reader = PyPDF2.PdfFileReader(file)
        total_pages = pdf_reader.numPages

        for i in range(0, total_pages, batch_size_pages):
            pdf_writer = PyPDF2.PdfFileWriter()
            output_filepath = output_filepath_template % page_number

            for page_number in range(i, min(i + batch_size_pages, total_pages)):
                print(f"Exporting page {page_number} to {output_file_path}")
                pdf_page = pdf_reader.getPage(page_number)
                pdf_writer.addPage(pdf_page)

            with open(output_filepath, "wb") as output_file:
                pdf_writer.write(output_file)
            batch_files.append(output_filepath)

    return batch_files


@dsl.component(base_image="python:3.11", packages_to_install=["openai", "tiktoken"])
def split_on_tokens_openai(
    text: Input[Artifact],
    output_filepath_template: str = "/tmp/split-%d.txt",
    model: str = "gpt-4",
    split_on: str = "\n",
    max_tokens: int = 1024,
) -> List[str]:
    import tiktoken
    import openai

    openai.api_key = openai_api_key

    encoding = tiktoken.encoding_for_model(model)

    with open(text.path, "r") as file:
        contents = file.read()
        if split_on:
            texts = contents.split(split_on)
        else:  # by default, split by word
            texts = contents.split()

    token_counts = {}
    for text in texts:
        token_counts[text] = len(encoding.encode(text))

    # Batch the texts based on token count
    # This is a greedy algorithm, so it will not be optimal
    batches = []
    in_progress_batch = {token_count: 0, contents: []}
    for text in token_counts.keys():
        if in_progress["token_count"] + token_counts[text] < max_tokens:
            in_progress_batch["contents"].append(text)
            in_progress_batch["token_count"] += token_counts[text]
        else:
            batches.append(in_progress_batch)
            in_progress_batch = {token_count: token_counts[text], contents: [text]}

    output_filepaths = []
    for i, batch in enumerate(batches):
        output_filepath = output_filepath_template % i
        with open(output_filepath, "w") as file:
            file.write(split_on.join(batch["contents"]))
        output_filepaths.append(output_filepath)

    return output_filepaths


@dsl.component(base_image="python:3.11", packages_to_install=["moviepy"])
def split_video_by_durations(
    video: Input[Artifact],
    seconds_per_part: int = 60,
    output_filepath_template: str = "/tmp/part-%d.png",
    video_codec: str = "libx264",
    audio_codec: str = "aac",
) -> List[str]:
    from moviepy.editor import VideoFileClip
    import math

    # Load the video file
    video = VideoFileClip(video.path)

    # Calculate the duration of the video in seconds
    duration = int(video.duration)

    # Calculate the number of parts the video will be split into
    parts = math.ceil(duration / seconds_per_part)

    # Split and export the video
    output_filepaths = []
    for part in range(parts):
        # Calculate start and end times for the current part
        start_time = part * 60
        end_time = (part + 1) * 60

        # Ensure end time does not exceed video duration
        end_time = min(end_time, duration)

        # Clip the video for the current part
        current_part = video.subclip(start_time, end_time)

        # Export the current part
        output_filepath = output_filepath_template % part
        current_part.write_videofile(
            output_filepath, codec=video_codec, audio_codec=audio_codec
        )
        output_filepaths.append(output_filepath)

    return output_filepaths


compiler.Compiler().compile(split_audio_on_silence, "split-audio-on-silence.yaml")
compiler.Compiler().compile(split_pdf_by_pages, "split-pdf-by-pages.yaml")
compiler.Compiler().compile(split_on_tokens_openai, "split-on-tokens-openai.yaml")
compiler.Compiler().compile(split_video_by_durations, "split-video-by-durations.yaml")
