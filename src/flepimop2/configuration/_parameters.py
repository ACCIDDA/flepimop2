from typing import Any, Literal

from pydantic import BaseModel, model_serializer, model_validator


class FixedParameterSpecificationModel(BaseModel):
    """
    Fixed parameter specification model.

    This model represents a parameter with a fixed value.

    Attributes:
        type: The type of the parameter specification, fixed to "fixed".
        value: The fixed numeric value of the parameter.

    Examples:
        >>> from flepimop2.configuration import FixedParameterSpecificationModel
        >>> param = FixedParameterSpecificationModel(value=12.34)
        >>> param
        FixedParameterSpecificationModel(type='fixed', value=12.34)
        >>> param.model_dump()
        12.34
    """

    type: Literal["fixed"] = "fixed"
    value: float

    @model_validator(mode="before")
    @classmethod
    def _coerce_parameter_specification(cls, value: Any) -> Any:  # noqa: ANN401
        if isinstance(value, (int, float)):
            return {"type": "fixed", "value": float(value)}
        return value

    @model_serializer
    def _serialize_as_number(self) -> float:
        """
        Serialize fixed parameters as just the numeric value.

        Returns:
            The numeric `value` of the fixed parameter.
        """
        return self.value


ParameterSpecificationModel = FixedParameterSpecificationModel
