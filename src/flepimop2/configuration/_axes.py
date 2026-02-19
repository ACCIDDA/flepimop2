__all__ = []

from typing import Annotated, Literal, Self

from pydantic import BaseModel, Field, model_validator

from flepimop2.configuration._types import IdentifierString


class ContinuousAxisModel(BaseModel):
    """
    Configuration model for a continuous (float) axis.

    Attributes:
        kind: Discriminator field; always `"continuous"`.
        domain: A `[lo, hi]` pair of floats defining the axis extent.
        size: Number of evenly-spaced points.  Required for continuous axes.
        spacing: Whether points are spaced `"linear"` or `"log"`-uniformly.

    Examples:
        >>> from flepimop2.configuration._axes import ContinuousAxisModel
        >>> ContinuousAxisModel(domain=(0.0, 12.0), size=5, spacing="linear")
        ContinuousAxisModel(kind='continuous', domain=(0.0, 12.0), size=5, spacing='linear')
    """  # noqa: E501

    kind: Literal["continuous"] = "continuous"
    domain: tuple[float, float]
    size: int = Field(gt=1)
    spacing: Literal["linear", "log"] = "linear"

    @model_validator(mode="after")
    def _validate_domain_and_size(self) -> Self:
        """
        Validate the domain and size of the axis.

        Returns:
            The validated `ContinuousAxisModel` instance.

        Raises:
            ValueError: If the lower bound of the domain is not less than the upper
                bound.
            ValueError: If `spacing` is `"log"` and the lower bound of the domain is
                not strictly positive.

        Examples:
            >>> from flepimop2.configuration._axes import ContinuousAxisModel
            >>> ContinuousAxisModel(domain=[0.0, 10.0], size=5)
            ContinuousAxisModel(kind='continuous', domain=(0.0, 10.0), size=5, spacing='linear')
            >>> ContinuousAxisModel(domain=[10.0, 0.0], size=5)
            Traceback (most recent call last):
                ...
            pydantic_core._pydantic_core.ValidationError: 1 validation error for ContinuousAxisModel
              Value error, lower bound, 10.0, must be strictly less than upper bound, 0.0 [...]
                For further information visit ...
            >>> ContinuousAxisModel(domain=[0.0, 0.0], size=5)
            Traceback (most recent call last):
                ...
            pydantic_core._pydantic_core.ValidationError: 1 validation error for ContinuousAxisModel
              Value error, lower bound, 0.0, must be strictly less than upper bound, 0.0 [...]
                For further information visit ...
            >>> ContinuousAxisModel(domain=[-1.0, 1.0], size=5, spacing="log")
            Traceback (most recent call last):
                ...
            pydantic_core._pydantic_core.ValidationError: 1 validation error for ContinuousAxisModel
              Value error, log spacing requires a strictly positive lower bound, given -1.0 [...]
                For further information visit ...
        """  # noqa: E501
        lo, hi = self.domain
        if lo >= hi:
            msg = f"lower bound, {lo}, must be strictly less than upper bound, {hi}"
            raise ValueError(msg)
        if self.spacing == "log" and lo <= 0:
            msg = f"log spacing requires a strictly positive lower bound, given {lo}"
            raise ValueError(msg)
        return self


class CategoricalAxisModel(BaseModel):
    """
    Configuration model for a categorical axis.

    Attributes:
        kind: Discriminator field; always `"categorical"`.
        labels: Ordered sequence of string category labels.
        values: Integer values associated with each label (e.g. for ordinal data
            or spline interpolation). Must be the same length as `labels`.
            Defaults to `1, 2, ..., N` where `N` is `len(labels)`.

    Examples:
        >>> from flepimop2.configuration._axes import CategoricalAxisModel
        >>> CategoricalAxisModel(labels=("foo", "bar", "baz"))
        CategoricalAxisModel(kind='categorical', labels=('foo', 'bar', 'baz'), values=(1, 2, 3))
    """  # noqa: E501

    kind: Literal["categorical"] = "categorical"
    labels: tuple[str, ...] = Field(min_length=1)
    values: tuple[int, ...] = Field(
        default_factory=lambda data: tuple(range(1, len(data["labels"]) + 1))
    )

    @model_validator(mode="after")
    def _validate_values_length(self) -> Self:
        """
        Validate that `values` have the same length as `labels`.

        Returns:
            The validated `CategoricalAxisModel` instance.

        Raises:
            ValueError: If `values` length does not match the length of `labels`.

        Examples:
            >>> from flepimop2.configuration._axes import CategoricalAxisModel
            >>> CategoricalAxisModel(labels=["a", "b"])
            CategoricalAxisModel(kind='categorical', labels=('a', 'b'), values=(1, 2))
            >>> CategoricalAxisModel(labels=["a", "b"], values=[1, 2])
            CategoricalAxisModel(kind='categorical', labels=('a', 'b'), values=(1, 2))
            >>> CategoricalAxisModel(labels=["a", "b"], values=[1])
            Traceback (most recent call last):
                ...
            pydantic_core._pydantic_core.ValidationError: 1 validation error for CategoricalAxisModel
              Value error, the length of 'values', 1, must match the length of 'labels', 2 [...]
                For further information visit ...
            >>> CategoricalAxisModel(labels=["a", "b"], values=[1, 2, 3])
            Traceback (most recent call last):
                ...
            pydantic_core._pydantic_core.ValidationError: 1 validation error for CategoricalAxisModel
              Value error, the length of 'values', 3, must match the length of 'labels', 2 [...]
                For further information visit ...

        """  # noqa: E501
        if (len_values := len(self.values)) != (len_labels := len(self.labels)):
            msg = (
                f"the length of 'values', {len_values}, must "
                f"match the length of 'labels', {len_labels}"
            )
            raise ValueError(msg)
        return self


AxisModel = Annotated[
    ContinuousAxisModel | CategoricalAxisModel,
    Field(discriminator="kind"),
]
"""Discriminated union of all axis configuration models."""

AxesGroupModel = dict[IdentifierString, AxisModel]
"""Type alias for the `axes` block in a configuration file."""
