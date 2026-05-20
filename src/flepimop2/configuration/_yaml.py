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
from collections import UserDict, UserList
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any, Self, TypeVar

from pydantic import BaseModel
from yaml import MappingNode, SafeDumper, SequenceNode
from yaml import dump as yaml_dump
from yaml import safe_load as yaml_safe_load

T = TypeVar("T")
K = TypeVar("K")
V = TypeVar("V")


class YamlFormattedSequence(UserList[T]):
    """
    List wrapper that can request a specific YAML flow style.

    Examples:
        >>> wrapped = YamlFormattedSequence((1, 2), flow_style=True)
        >>> list(wrapped)
        [1, 2]
        >>> wrapped.flow_style
        True
    """

    __slots__ = ("flow_style",)

    def __init__(
        self,
        values: Iterable[T] = (),
        *,
        flow_style: bool | None = None,
    ) -> None:
        super().__init__(values)
        self.flow_style = flow_style


class YamlFormattedMapping(UserDict[K, V]):
    """
    Dict wrapper that can request a specific YAML flow style.

    Examples:
        >>> wrapped = YamlFormattedMapping({"a": 1}, flow_style=True)
        >>> dict(wrapped)
        {'a': 1}
        >>> wrapped.flow_style
        True
    """

    __slots__ = ("flow_style",)

    def __init__(
        self,
        values: Mapping[K, V] | Iterable[tuple[K, V]] = (),
        *,
        flow_style: bool | None = None,
    ) -> None:
        super().__init__(values)
        self.flow_style = flow_style


def yaml_sequence(
    values: Iterable[T] = (),
    *,
    flow_style: bool | None = None,
) -> YamlFormattedSequence[T]:
    """
    Wrap a sequence with YAML style metadata.

    Module authors can return this from `to_yaml_data()` when a specific
    subtree should use flow style, e.g. `[a, b, c]`.

    Returns:
        A sequence wrapper carrying the requested YAML flow-style hint.

    Examples:
        >>> wrapped = yaml_sequence(("a", "b"), flow_style=True)
        >>> list(wrapped)
        ['a', 'b']
        >>> wrapped.flow_style
        True
    """
    return YamlFormattedSequence(values, flow_style=flow_style)


def yaml_mapping(
    values: Mapping[K, V] | Iterable[tuple[K, V]] = (),
    *,
    flow_style: bool | None = None,
) -> YamlFormattedMapping[K, V]:
    """
    Wrap a mapping with YAML style metadata.

    Module authors can return this from `to_yaml_data()` when a specific
    subtree should use flow style, e.g. `{a: 1, b: 2}`.

    Returns:
        A mapping wrapper carrying the requested YAML flow-style hint.

    Examples:
        >>> wrapped = yaml_mapping({"kind": "demo"}, flow_style=True)
        >>> dict(wrapped)
        {'kind': 'demo'}
        >>> wrapped.flow_style
        True
    """
    return YamlFormattedMapping(values, flow_style=flow_style)


class Flepimop2YamlDumper(SafeDumper):
    """Project YAML dumper with support for per-subtree flow-style wrappers."""


def _represent_yaml_formatted_sequence(
    dumper: SafeDumper,
    data: YamlFormattedSequence[object],
) -> SequenceNode:
    """
    Represent a wrapped sequence using its requested flow style.

    Returns:
        A YAML sequence node with the requested flow-style setting.
    """
    return dumper.represent_sequence(
        "tag:yaml.org,2002:seq",
        data.data,
        flow_style=data.flow_style,
    )


def _represent_yaml_formatted_mapping(
    dumper: SafeDumper,
    data: YamlFormattedMapping[object, object],
) -> MappingNode:
    """
    Represent a wrapped mapping using its requested flow style.

    Returns:
        A YAML mapping node with the requested flow-style setting.
    """
    return dumper.represent_mapping(
        "tag:yaml.org,2002:map",
        data.data,
        flow_style=data.flow_style,
    )


Flepimop2YamlDumper.add_representer(
    YamlFormattedSequence,
    _represent_yaml_formatted_sequence,
)
Flepimop2YamlDumper.add_representer(
    YamlFormattedMapping,
    _represent_yaml_formatted_mapping,
)


def _model_to_yaml_mapping(model: BaseModel) -> dict[str, object]:
    """
    Convert a Pydantic model to a YAML-ready mapping without dumping it first.

    Returns:
        A recursively normalized mapping representation of the model.

    Examples:
        >>> class DemoModel(BaseModel):
        ...     name: str
        ...     dims: tuple[int, int]
        >>> _model_to_yaml_mapping(DemoModel(name="demo", dims=(1, 2)))
        {'name': 'demo', 'dims': [1, 2]}
    """
    data = {
        field_name: _to_yaml_data(getattr(model, field_name))
        for field_name in type(model).model_fields
    }
    if model.model_extra:
        data.update({
            field_name: _to_yaml_data(value)
            for field_name, value in model.model_extra.items()
        })
    return data


def _to_yaml_data(value: object) -> object:
    """
    Recursively convert models and containers into YAML-ready Python values.

    Returns:
        A YAML-ready scalar or container.

    Examples:
        >>> class DemoModel(YamlSerializableBaseModel):
        ...     name: str
        >>> _to_yaml_data({
        ...     "items": yaml_sequence((1, 2), flow_style=True),
        ...     "model": DemoModel(name="demo"),
        ... })
        {'items': [1, 2], 'model': {'name': 'demo'}}
    """
    result = value
    if isinstance(value, BaseModel):
        formatter = getattr(value, "to_yaml_data", None)
        if callable(formatter):
            result = _to_yaml_data(formatter())
        else:
            result = _model_to_yaml_mapping(value)
    elif isinstance(value, YamlFormattedSequence):
        result = type(value)(
            (_to_yaml_data(item) for item in value),
            flow_style=value.flow_style,
        )
    elif isinstance(value, YamlFormattedMapping):
        result = type(value)(
            ((key, _to_yaml_data(item)) for key, item in value.items()),
            flow_style=value.flow_style,
        )
    elif isinstance(value, list | tuple):
        result = [_to_yaml_data(item) for item in value]
    elif isinstance(value, dict):
        result = {key: _to_yaml_data(item) for key, item in value.items()}
    return result


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

        Examples:
            >>> class DemoModel(YamlSerializableBaseModel):
            ...     name: str
            >>> DemoModel.safe_load("name: demo")
            DemoModel(name='demo')
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

        Examples:
            >>> class DemoModel(YamlSerializableBaseModel):
            ...     name: str
            >>> print(DemoModel(name="demo").safe_dump(), end="")
            name: demo
        """
        return yaml_dump(
            self.to_yaml_data(),
            Dumper=Flepimop2YamlDumper,
            default_flow_style=False,
            sort_keys=False,
        )

    def to_yaml_data(self) -> object:
        """
        Convert the model into YAML-ready Python objects.

        Subclasses can override this method to control both the serialized
        representation and any YAML style wrappers used by the project dumper.

        Returns:
            A YAML-ready representation of the model.

        Examples:
            >>> class DemoModel(YamlSerializableBaseModel):
            ...     name: str
            ...     dims: tuple[int, int]
            >>> DemoModel(name="demo", dims=(1, 2)).to_yaml_data()
            {'name': 'demo', 'dims': [1, 2]}
        """
        return _model_to_yaml_mapping(self)

    def to_yaml(self, file: Path, encoding: str = "utf-8", **kwargs: Any) -> None:
        """
        Serialize the model to a YAML file.

        Args:
            file: Path to the YAML file to write.
            encoding: Encoding of the YAML file.
            **kwargs: Additional keyword arguments to pass to `Path.write_text`.
        """
        file.write_text(self.safe_dump(), encoding=encoding, **kwargs)
