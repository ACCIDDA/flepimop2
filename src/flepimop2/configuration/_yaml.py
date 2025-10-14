from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import BaseModel
from yaml import safe_dump, safe_load

if TYPE_CHECKING:
    import sys

    if sys.version_info >= (3, 11):
        from typing import Self
    else:
        from typing_extensions import Self


class YamlSerializableBaseModel(BaseModel):
    """Base model with YAML serialization support."""

    @classmethod
    def from_yaml(cls, file: Path, encoding: str = "utf-8") -> "Self":
        """
        Deserialize a YAML string to an instance of the model.

        Args:
            file: Path to the YAML file to read.
            encoding: Encoding of the YAML file.

        Returns:
            An instance of the model.
        """
        return cls.model_validate(safe_load(file.read_text(encoding=encoding)))

    def to_yaml(self, file: Path, encoding: str = "utf-8") -> None:
        """
        Serialize the model to a YAML string.

        Args:
            file: Path to the YAML file to read.
            encoding: Encoding of the YAML file.
        """
        with file.open("w", encoding=encoding) as f:
            safe_dump(self.model_dump(), stream=f, encoding=encoding)
