from abc import ABC, abstractmethod
from pathlib import Path

class ReverseImageSearchProvider(ABC):
    name = "base"

    @abstractmethod
    def search(self, image_path: Path, max_results: int = None):
        raise NotImplementedError
