import kfp.dsl as dsl

from kfp import compiler
from typing import List


@dsl.component(base_image="python:3.11")
def find_files(directory: str, regexp: str) -> List[str]:
    import os
    import re

    matching_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if re.match(regexp, file) and not file.startswith("."):
                matching_files.append(os.path.join(root, file))

    return matching_files


compiler.Compiler().compile(find_files, "find-files.yaml")
