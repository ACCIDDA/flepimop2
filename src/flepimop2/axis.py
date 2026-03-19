"""Runtime axis types and helpers."""

__all__ = ["Axis", "AxisCollection", "ResolvedAxisConfig", "ResolvedShape"]

from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from itertools import pairwise
from typing import Literal, TypeVar, overload

import numpy as np
from pydantic import TypeAdapter

from flepimop2.configuration._axes import (
    AxesGroupModel,
    CategoricalAxisModel,
    ContinuousAxisModel,
)
from flepimop2.configuration._types import IdentifierString

ResolvedAxisConfig = (
    AxesGroupModel | Mapping[IdentifierString, object] | dict[IdentifierString, object]
)
T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class ResolvedShape:
    """A named runtime shape resolved against a concrete axis collection."""

    axis_names: tuple[IdentifierString, ...] = ()
    sizes: tuple[int, ...] = ()

    def __post_init__(self) -> None:
        """
        Validate the number of axis names and sizes match.

        Raises:
            ValueError: If `axis_names` and `sizes` do not have matching lengths.

        Examples:
            >>> from flepimop2.axis import ResolvedShape
            >>> ResolvedShape(axis_names=("age", "time"), sizes=(3, 4))
            ResolvedShape(axis_names=('age', 'time'), sizes=(3, 4))
            >>> ResolvedShape(axis_names=("age",), sizes=(3, 4))
            Traceback (most recent call last):
                ...
            ValueError: ResolvedShape axis_names and sizes must have matching lengths; got 1 names and 2 sizes.
        """  # noqa: E501
        if len(self.axis_names) != len(self.sizes):
            msg = (
                "ResolvedShape axis_names and sizes must have matching lengths; "
                f"got {len(self.axis_names)} names and {len(self.sizes)} sizes."
            )
            raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class Axis:
    """
    Resolved Runtime Axis.

    Describe one named axis after configuration has been validated and converted
    into runtime metadata.

    Attributes:
        name: Stable axis name used by systems and parameters.
        kind: Whether the axis is continuous or categorical.
        size: Number of positions along the axis.
        labels: Optional labels for categorical axes.
        values: Optional integer values associated with categorical labels.
        domain: Closed numeric domain for continuous axes.
        spacing: Spacing rule for continuous axes.

    Notes:
        Continuous axes intentionally support both point-style and bin-style
        calculations. The same axis can expose representative points via
        `points()` and intervals via `bins()`, so systems and parameters can use
        whichever view is appropriate without introducing incompatible axis
        definitions.
    """

    name: IdentifierString
    kind: Literal["continuous", "categorical"]
    size: int
    labels: tuple[str, ...] | None = None
    values: tuple[int, ...] | None = None
    domain: tuple[float, float] | None = None
    spacing: Literal["linear", "log"] | None = None

    def _continuous_domain(self) -> tuple[float, float]:
        """
        Validate Continuous Axis Metadata.

        Ensure this axis can support continuous point and bin helpers.

        Returns:
            The continuous axis domain as `(lower, upper)`.

        Raises:
            TypeError: If this is not a continuous axis.
            ValueError: If the continuous axis is missing domain or spacing
                metadata.

        Examples:
            >>> from flepimop2.axis import Axis
            >>> axis = Axis(
            ...     name="time",
            ...     kind="continuous",
            ...     size=4,
            ...     domain=(0.0, 8.0),
            ...     spacing="linear",
            ... )
            >>> axis._continuous_domain()
            (0.0, 8.0)
            >>> Axis(name="age", kind="categorical", size=2)._continuous_domain()
            Traceback (most recent call last):
                ...
            TypeError: Axis 'age' is 'categorical'; only continuous axes support point and bin helpers.
            >>> Axis(
            ...     name="time",
            ...     kind="continuous",
            ...     size=4,
            ... )._continuous_domain()
            Traceback (most recent call last):
                ...
            ValueError: Continuous axis 'time' must define both domain and spacing to derive point or bin helpers.
        """  # noqa: E501
        if self.kind != "continuous":
            msg = (
                f"Axis '{self.name}' is {self.kind!r}; only continuous axes "
                "support point and bin helpers."
            )
            raise TypeError(msg)
        if self.domain is None or self.spacing is None:
            msg = (
                f"Continuous axis '{self.name}' must define both domain and "
                "spacing to derive point or bin helpers."
            )
            raise ValueError(msg)
        return self.domain

    def bin_edges(self) -> tuple[float, ...]:
        """
        Continuous Bin Edges.

        Partition a continuous axis domain into `size` bins.

        Returns:
            The bin-edge coordinates with length `size + 1`.

        Notes:
            Linear axes use `np.linspace(lower, upper, size + 1)`. Log axes use
            `np.geomspace(lower, upper, size + 1)`.

        Examples:
            >>> from flepimop2.axis import Axis
            >>> axis = Axis(
            ...     name="time",
            ...     kind="continuous",
            ...     size=4,
            ...     domain=(0.0, 8.0),
            ...     spacing="linear",
            ... )
            >>> axis.bin_edges()
            (0.0, 2.0, 4.0, 6.0, 8.0)
        """
        lo, hi = self._continuous_domain()
        if self.spacing == "linear":
            edges = np.linspace(lo, hi, self.size + 1, dtype=np.float64)
        else:
            edges = np.geomspace(lo, hi, self.size + 1, dtype=np.float64)
        return tuple(edges.tolist())

    def bins(self) -> tuple[tuple[float, float], ...]:
        """
        Continuous Bin Intervals.

        Return half-open-style interval metadata for each continuous bin.

        Returns:
            A tuple of `(lower, upper)` bin intervals with length `size`.

        Examples:
            >>> from flepimop2.axis import Axis
            >>> axis = Axis(
            ...     name="time",
            ...     kind="continuous",
            ...     size=2,
            ...     domain=(0.0, 4.0),
            ...     spacing="linear",
            ... )
            >>> axis.bins()
            ((0.0, 2.0), (2.0, 4.0))
        """
        self._continuous_domain()
        edges = self.bin_edges()
        return tuple(pairwise(edges))

    def points(self) -> tuple[float, ...]:
        """
        Representative Continuous Points.

        Return one representative point for each continuous bin.

        Returns:
            A tuple of representative point coordinates with length `size`.

        Notes:
            Points are sampled directly from the configured domain using
            `np.linspace(lower, upper, size, endpoint=False)` or
            `np.geomspace(lower, upper, size, endpoint=False)`. This keeps
            point- and bin-based views available from the same runtime axis
            metadata while avoiding duplication of the upper domain bound.

        Examples:
            >>> from pprint import pp
            >>> from flepimop2.axis import Axis
            >>> Axis(
            ...     name="time",
            ...     kind="continuous",
            ...     size=4,
            ...     domain=(0.0, 8.0),
            ...     spacing="linear",
            ... ).points()
            (1.0, 3.0, 5.0, 7.0)
            >>> pp(
            ...     Axis(
            ...         name="time",
            ...         kind="continuous",
            ...         size=4,
            ...         domain=(1e-9, 1e-3),
            ...         spacing="log",
            ...     ).points()
            ... )
            (5.623413251903491e-09,
             1.7782794100389227e-07,
             5.623413251903491e-06,
             0.0001778279410038923)
        """
        lo, hi = self._continuous_domain()
        if self.spacing == "linear":
            edges = np.linspace(lo, hi, self.size + 1, dtype=np.float64)
            points = 0.5 * (edges[:-1] + edges[1:])
        else:
            edges = np.geomspace(lo, hi, self.size + 1, dtype=np.float64)
            points = np.sqrt(edges[:-1] * edges[1:])
        return tuple(points.tolist())

    @classmethod
    def from_model(
        cls,
        name: IdentifierString,
        model: ContinuousAxisModel | CategoricalAxisModel,
    ) -> "Axis":
        """
        Build an `Axis` from a configuration model.

        Returns:
            The resolved runtime axis.
        """
        if isinstance(model, ContinuousAxisModel):
            return cls(
                name=name,
                kind=model.kind,
                size=model.size,
                domain=model.domain,
                spacing=model.spacing,
            )
        return cls(
            name=name,
            kind=model.kind,
            size=len(model.labels),
            labels=model.labels,
            values=model.values,
        )


class AxisCollection(Mapping[IdentifierString, Axis]):
    """
    Runtime Axis Collection.

    Store resolved axes and provide lookup and named-shape helpers for systems,
    parameters, and engines.

    Notes:
        `AxisCollection` is the runtime entry point for working with named axes.
        Systems typically use it to resolve requested parameter shapes, while
        parameter modules use it to interpret declared axis names and inspect
        axis metadata such as labels or bin edges.

    Examples:
        >>> from flepimop2.axis import AxisCollection
        >>> axes = AxisCollection.from_config({
        ...     "age": {
        ...         "kind": "categorical",
        ...         "labels": ["age0_17", "age18_64", "age65_plus"],
        ...     },
        ...     "time": {
        ...         "kind": "continuous",
        ...         "domain": (0.0, 12.0),
        ...         "size": 4,
        ...     },
        ... })
        >>> axes.size("age")
        3
        >>> axes["age"].labels
        ('age0_17', 'age18_64', 'age65_plus')
        >>> axes["time"].bin_edges()
        (0.0, 3.0, 6.0, 9.0, 12.0)
        >>> axes.resolve_shape(("age", "time")).sizes
        (3, 4)
        >>> axes.resolve_shape(("region",))
        Traceback (most recent call last):
            ...
        KeyError: "Unknown axis names requested: ('region',)."
    """

    def __init__(self, axes: Mapping[IdentifierString, Axis] | None = None) -> None:
        """Initialize the collection with an optional axis mapping."""
        self._axes = dict(axes or {})

    @classmethod
    def from_config(cls, config: ResolvedAxisConfig) -> "AxisCollection":
        """
        Construct a runtime axis collection from configuration data.

        Returns:
            The resolved runtime axis collection.
        """
        validated = TypeAdapter(AxesGroupModel).validate_python(config)
        return cls({
            name: Axis.from_model(name, axis) for name, axis in validated.items()
        })

    def __getitem__(self, key: IdentifierString) -> Axis:
        """Return the axis for a given name."""
        return self._axes[key]

    def __iter__(self) -> Iterator[IdentifierString]:
        """
        Iterate over axis names in the collection.

        Returns:
            An iterator over axis names.
        """
        return iter(self._axes)

    def __len__(self) -> int:
        """Return the number of axes in the collection."""
        return len(self._axes)

    @overload
    def get(self, name: IdentifierString, /) -> Axis | None: ...

    @overload
    def get(self, name: IdentifierString, /, default: Axis) -> Axis: ...

    @overload
    def get(self, name: IdentifierString, /, default: T) -> Axis | T: ...

    def get(
        self, name: IdentifierString, /, default: T | None = None
    ) -> Axis | T | None:
        """
        Return a named axis, optionally providing a default.

        Returns:
            The resolved axis, or the provided default when missing.
        """
        return self._axes.get(name, default)

    def size(self, name: IdentifierString) -> int:
        """Return the size for a named axis."""
        return self[name].size

    def sizes(self, *names: IdentifierString) -> tuple[int, ...]:
        """Return the sizes for a sequence of named axes."""
        return tuple(self.size(name) for name in names)

    def resolve_shape(self, axis_names: Sequence[IdentifierString]) -> ResolvedShape:
        """
        Resolve a tuple of axis names into concrete dimension sizes.

        Returns:
            The resolved named shape.
        """
        names = tuple(axis_names)
        self._validate_axis_names(names)
        return ResolvedShape(axis_names=names, sizes=self.sizes(*names))

    def _validate_axis_names(self, axis_names: Sequence[IdentifierString]) -> None:
        """
        Validate that each named axis exists in the collection.

        Raises:
            KeyError: If any requested axis name does not exist.
        """
        missing = tuple(name for name in axis_names if name not in self._axes)
        if missing:
            msg = f"Unknown axis names requested: {missing}."
            raise KeyError(msg)
