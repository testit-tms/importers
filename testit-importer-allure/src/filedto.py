"""The module describes file dto"""
from typing import IO
import dataclasses


@dataclasses.dataclass
class FileDto:
    """Class representing a file dto"""

    def __init__(self, name: str, file: IO):
        self.name = name
        self.file = file
