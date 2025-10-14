"""Unit tests for the `FixedParameterSpecificationModel` class."""

import math
from pathlib import Path

from yaml import safe_load

from flepimop2.configuration import FixedParameterSpecificationModel
from flepimop2.configuration._yaml import YamlSerializableBaseModel


class SerializedFixedParameterExampleModel(YamlSerializableBaseModel):
    """Example model for testing serialization of FixedParameterSpecificationModel."""

    parameter: FixedParameterSpecificationModel


def test_fixed_parameter_serialized_as_number(tmp_path: Path) -> None:
    """Test that a fixed parameter specified as a number is correctly serialized."""
    model = SerializedFixedParameterExampleModel.model_validate({"parameter": math.pi})
    assert isinstance(model.parameter, FixedParameterSpecificationModel)
    yaml_path = tmp_path / "fixed_parameter.yaml"
    model.to_yaml(yaml_path)
    contents = safe_load(yaml_path.read_text())
    assert contents == {"parameter": math.pi}
