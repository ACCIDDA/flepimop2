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
from typing import Any, Self

from pydantic import BaseModel
from yaml import safe_dump as yaml_safe_dump
from yaml import safe_load as yaml_safe_load


class YamlSerializableBaseModel(BaseModel):
    """
    Base model with YAML serialization support.

    Example:
        >>> class DemoModel(YamlSerializableBaseModel):
        ...     name: str
        >>> payload = DemoModel(name="demo").safe_dump()
        >>> print(payload, end="")
        name: demo
        >>> DemoModel.safe_load(payload)
        DemoModel(name='demo')
    """

    @classmethod
    def safe_load(cls, contents: str) -> Self:
        """
        Deserialize YAML text to an instance of the model.

        Args:
            contents: The YAML document to deserialize.

        Returns:
            An instance of the model.
        """
        return cls.model_validate(yaml_safe_load(contents))

    @classmethod
    def from_yaml(cls, file: Path, encoding: str = "utf-8", **kwargs: Any) -> Self:
        """
        Deserialize a YAML file to an instance of the model.

        Args:
            file: Path to the YAML file to read.
            encoding: Encoding of the YAML file.
            **kwargs: Additional keyword arguments to pass to `Path.read_text`.

        Returns:
            An instance of the model.
        """
        return cls.safe_load(file.read_text(encoding=encoding, **kwargs))

    def safe_dump(self) -> str:
        """
        Serialize the model to a YAML document.

        Returns:
            The serialized YAML document.
        """
        return yaml_safe_dump(self.model_dump(), sort_keys=False)

    def to_yaml(self, file: Path, encoding: str = "utf-8", **kwargs: Any) -> None:
        """
        Serialize the model to a YAML file.

        Args:
            file: Path to the YAML file to write.
            encoding: Encoding of the YAML file.
            **kwargs: Additional keyword arguments to pass to `Path.write_text`.
        """
        file.write_text(self.safe_dump(), encoding=encoding, **kwargs)
