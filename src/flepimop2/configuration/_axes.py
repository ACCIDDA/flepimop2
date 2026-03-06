"""Axis configuration models and the `Axis` NamedTuple."""

__all__ = ["AxesGroupModel", "Axis", "AxisModel"]

from typing import Annotated, Literal, NamedTuple, Self

import numpy as np
from pydantic import BaseModel, Field, model_validator

from flepimop2.configuration._types import IdentifierString
from flepimop2.typing import Float64NDArray


class Axis(NamedTuple):
    """
    Resolved axis used internally throughout flepimop2.

    Attributes:
        name: The axis name, taken from the key in the `axes` config dict.
        kind: The kind of axis (`"continuous"`, `"integer"`, or `"categorical"`).
        labels: Ordered string labels for every point on the axis.
        values: Numeric values corresponding to each label.  Always populated for
            `"continuous"` and `"integer"` axes; `None` for `"categorical"` axes whose
            config did not supply values.

    Examples:
        >>> from flepimop2.configuration._axes import Axis
        >>> age = Axis(
        ...     name="age", kind="integer", labels=("0", "1", "2"), values=(0, 1, 2)
        ... )
        >>> age
        Axis(name='age', kind='integer', labels=('0', '1', '2'), values=(0, 1, 2))
        >>> len(age)
        3
        >>> age == Axis(
        ...     name="age", kind="integer", labels=("0", "1", "2"), values=(0, 1, 2)
        ... )
        True
        >>> age == Axis(
        ...     name="years",
        ...     kind="integer",
        ...     labels=("0", "1", "2"),
        ...     values=(0, 1, 2),
        ... )
        False
        >>> age == Axis(
        ...     name="age",
        ...     kind="integer",
        ...     labels=("0", "1", "2", "3"),
        ...     values=(0, 1, 2, 3),
        ... )
        False

    """

    name: str
    kind: Literal["continuous", "integer", "categorical"]
    labels: tuple[str, ...]
    values: tuple[int, ...] | tuple[float, ...] | None

    def __len__(self) -> int:
        """Return the number of points on this axis.

        This is equivalent to `len(self.labels)`.

        Examples:
            >>> from flepimop2.configuration._axes import Axis
            >>> ax = Axis(
            ...     name="age", kind="integer", labels=("0", "1", "2"), values=(0, 1, 2)
            ... )
            >>> len(ax)
            3
            >>> ax = Axis(
            ...     name="group",
            ...     kind="categorical",
            ...     labels=("high", "low"),
            ...     values=None,
            ... )
            >>> len(ax)
            2

        """
        return len(self.labels)


class _NumericAxisModel(BaseModel):
    """Shared validation logic for continuous and integer axes."""

    domain: tuple[float, float] | tuple[int, int]
    size: int | None = None
    spacing: Literal["linear", "log"] = "linear"

    @model_validator(mode="after")
    def _validate_domain_and_size(self) -> Self:
        """
        Validate the domain and size of the axis.

        Returns:
            The validated `_NumericAxisModel` instance.

        Raises:
            ValueError: If the lower bound of the domain is not less than the upper
                bound.
            ValueError: If `spacing` is `"log"` and the lower bound of the domain is
                not strictly positive.

        Examples:
            >>> from flepimop2.configuration._axes import _NumericAxisModel
            >>> _NumericAxisModel(domain=[0.0, 10.0], size=5)
            _NumericAxisModel(domain=(0.0, 10.0), size=5, spacing='linear')
            >>> _NumericAxisModel(domain=[10.0, 0.0], size=5)
            Traceback (most recent call last):
                ...
            pydantic_core._pydantic_core.ValidationError: 1 validation error for _NumericAxisModel
              Value error, lower bound, 10.0, must be strictly less than upper bound, 0.0 [...]
                For further information visit ...
            >>> _NumericAxisModel(domain=[0.0, 0.0], size=5)
            Traceback (most recent call last):
                ...
            pydantic_core._pydantic_core.ValidationError: 1 validation error for _NumericAxisModel
              Value error, lower bound, 0.0, must be strictly less than upper bound, 0.0 [...]
                For further information visit ...
            >>> _NumericAxisModel(domain=[-1.0, 1.0], size=5, spacing="log")
            Traceback (most recent call last):
                ...
            pydantic_core._pydantic_core.ValidationError: 1 validation error for _NumericAxisModel
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

    def _spacing_array(self, size: int) -> Float64NDArray:
        """
        Return an array of `size` evenly-spaced points over `domain`.

        Args:
            size: Number of points to generate.

        Returns:
            A float64 array of `size` values spanning `[lo, hi]`.

        """
        lo, hi = self.domain
        if self.spacing == "linear":
            return np.linspace(lo, hi, size)
        return np.geomspace(lo, hi, size)


class ContinuousAxisModel(_NumericAxisModel):
    """
    Configuration model for a continuous (float) axis.

    Attributes:
        kind: Discriminator field; always `"continuous"`.
        domain: A `[lo, hi]` pair of floats defining the axis extent.
        size: Number of evenly-spaced points.  Required for continuous axes.
        spacing: Whether points are spaced `"linear"` or `"log"`-uniformly.

    Examples:
        >>> from flepimop2.configuration._axes import ContinuousAxisModel
        >>> m = ContinuousAxisModel(domain=[0.0, 12.0], size=5, spacing="linear")
        >>> m.to_axis("space_x")
        Axis(name='space_x', kind='continuous', labels=('0.0', '3.0', '6.0', '9.0', '12.0'), values=(0.0, 3.0, 6.0, 9.0, 12.0))

    """  # noqa: E501

    kind: Literal["continuous"] = "continuous"
    domain: tuple[float, float]
    size: int = Field(gt=1)

    def to_axis(self, name: str) -> Axis:
        """
        Convert this model to an `Axis` NamedTuple.

        Args:
            name: The axis name (i.e. the dict key from the config).

        Returns:
            A fully-resolved `Axis` instance.
        """
        values: tuple[float, ...] = tuple(
            float(v) for v in self._spacing_array(self.size)
        )
        labels: tuple[str, ...] = tuple(str(v) for v in values)
        return Axis(name=name, kind="continuous", labels=labels, values=values)


class IntegerAxisModel(_NumericAxisModel):
    """
    Configuration model for an integer axis.

    When `size` is `None` every integer in `[lo, hi]` is included.

    Attributes:
        kind: Discriminator field; always `"integer"`.
        domain: A `[lo, hi]` pair of ints defining the axis extent (inclusive).
        size: Number of points.  `None` means every integer in the domain.
        spacing: Whether points are spaced `"linear"` or `"log"`-uniformly.

    Examples:
        >>> from flepimop2.configuration._axes import IntegerAxisModel
        >>> m = IntegerAxisModel(domain=[0, 10], size=None)
        >>> ax = m.to_axis("age")
        >>> ax.labels[:3]
        ('0', '1', '2')
        >>> ax.values[:3]
        (0, 1, 2)

    """

    kind: Literal["integer"] = "integer"
    domain: tuple[int, int]
    size: int | None = Field(default=None, gt=1)

    def to_axis(self, name: str) -> Axis:
        """
        Convert this model to an `Axis` NamedTuple.

        Args:
            name: The axis name (i.e. the dict key from the config).

        Returns:
            A fully-resolved `Axis` instance.

        """
        lo, hi = self.domain
        vals: tuple[int, ...] = (
            tuple(range(lo, hi + 1))
            if self.size is None
            else tuple(round(v) for v in self._spacing_array(self.size))
        )
        labels: tuple[str, ...] = tuple(str(v) for v in vals)
        return Axis(name=name, kind="integer", labels=labels, values=vals)


class CategoricalAxisModel(BaseModel):
    """
    Configuration model for a categorical axis.

    Attributes:
        kind: Discriminator field; always `"categorical"`.
        labels: Ordered sequence of string category labels.
        values: Optional numeric values associated with each label (e.g. for
            ordinal data or spline interpolation).  When provided, must be the
            same length as `labels`.

    Examples:
        >>> from flepimop2.configuration._axes import CategoricalAxisModel
        >>> m = CategoricalAxisModel(labels=["foo", "bar", "baz"])
        >>> m.to_axis("group")
        Axis(name='group', kind='categorical', labels=('foo', 'bar', 'baz'), values=None)

        >>> m2 = CategoricalAxisModel(
        ...     labels=["mild", "moderate", "severe"], values=[1.0, 3.0, 7.0]
        ... )
        >>> m2.to_axis("severity")
        Axis(name='severity', kind='categorical', labels=('mild', 'moderate', 'severe'), values=(1.0, 3.0, 7.0))

    """  # noqa: E501

    kind: Literal["categorical"] = "categorical"
    labels: tuple[str, ...] = Field(min_length=1)
    values: tuple[float, ...] | None = None

    @model_validator(mode="after")
    def _validate_values_length(self) -> Self:
        """
        Validate that if `values` are provided, they have the same length as `labels`.

        Returns:
            The validated `CategoricalAxisModel` instance.

        Raises:
            ValueError: If `values` is not `None` and its length does not match
                the length of `labels`.

        Examples:
            >>> from flepimop2.configuration._axes import CategoricalAxisModel
            >>> CategoricalAxisModel(labels=["a", "b"])
            CategoricalAxisModel(kind='categorical', labels=('a', 'b'), values=None)
            >>> CategoricalAxisModel(labels=["a", "b"], values=[1.0, 2.0])
            CategoricalAxisModel(kind='categorical', labels=('a', 'b'), values=(1.0, 2.0))
            >>> CategoricalAxisModel(labels=["a", "b"], values=[1.0])
            Traceback (most recent call last):
                ...
            pydantic_core._pydantic_core.ValidationError: 1 validation error for CategoricalAxisModel
              Value error, the length of 'values', 1, must match the length of 'labels', 2 [...]
                For further information visit ...
            >>> CategoricalAxisModel(labels=["a", "b"], values=[1.0, 2.0, 3.0])
            Traceback (most recent call last):
                ...
            pydantic_core._pydantic_core.ValidationError: 1 validation error for CategoricalAxisModel
              Value error, the length of 'values', 3, must match the length of 'labels', 2 [...]
                For further information visit ...

        """  # noqa: E501
        if self.values is not None and (len_values := len(self.values)) != (
            len_labels := len(self.labels)
        ):
            msg = (
                f"the length of 'values', {len_values}, must "
                f"match the length of 'labels', {len_labels}"
            )
            raise ValueError(msg)
        return self

    def to_axis(self, name: str) -> Axis:
        """
        Convert this model to an `Axis` NamedTuple.

        Args:
            name: The axis name (i.e. the dict key from the config).

        Returns:
            A fully-resolved `Axis` instance.

        """
        return Axis(
            name=name,
            kind="categorical",
            labels=self.labels,
            values=self.values,
        )


AxisModel = Annotated[
    ContinuousAxisModel | IntegerAxisModel | CategoricalAxisModel,
    Field(discriminator="kind"),
]
"""Discriminated union of all axis configuration models."""

AxesGroupModel = dict[IdentifierString, AxisModel]
"""Type alias for the `axes` block in a configuration file."""
