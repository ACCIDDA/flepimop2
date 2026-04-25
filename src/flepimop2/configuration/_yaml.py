# flepimop2: The FLExible Pipeline for Interchangeable MOdel Processing
# Copyright (C) 2026  Carl Pearson, Joshua Macdonald, Timothy Willard
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
from pathlib import Path
from typing import Self

from pydantic import BaseModel
from yaml import safe_dump, safe_load


class YamlSerializableBaseModel(BaseModel):
    """Base model with YAML serialization support."""

    @classmethod
    def from_yaml(cls, file: Path, encoding: str = "utf-8") -> Self:
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
