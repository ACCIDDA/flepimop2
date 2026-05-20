# Customizing Module Appearances

This guide shows how developers can control how a custom module appears when `flepimop2` serializes configuration back to YAML.

There are two layers involved:

- The Python-side representation returned by `ModuleBase.to_yaml_data()`.
- The YAML formatting hints attached to parts of that representation.

In practice, most external developers will not inherit directly from `ModuleBase`. They will usually inherit from one of the domain ABCs such as `ParameterABC`, `SystemABC`, `EngineABC`, or `BackendABC`. Those classes all inherit from `ModuleBase`, so the same `to_yaml_data()` hook applies there.

In most cases you should override `to_yaml_data()` on that domain-specific subclass. That lets you keep validation and patch behavior unchanged while still adjusting the user-facing YAML shape.

## 1. Start with the Default Behavior

By default, `ModuleBase.to_yaml_data()` returns a YAML-ready mapping based on the module fields. Empty `options` are omitted automatically.

For example:

```python
from flepimop2.parameter.abc import ParameterABC


class DemoParameter(ParameterABC, module="demo"):
    values: tuple[float, ...]

    def sample(self, *, axes=None, request=None):
        raise NotImplementedError
```

An instance like `DemoParameter(values=(0.1, 0.2, 0.3))` will serialize its fields using the default block-style YAML layout unless you override `to_yaml_data()`.

## 2. Override `to_yaml_data()` for User-Facing Control

Use `super().to_yaml_data()` as your starting point, then replace individual fields with the structure you want users to see:

```python
from flepimop2.configuration import yaml_mapping, yaml_sequence
from flepimop2.parameter.abc import ParameterABC


class LookupParameter(ParameterABC, module="lookup"):
    values: tuple[float, ...]
    bounds: tuple[int, int]
    shape: tuple[str, ...] = ()
    labels: tuple[str, ...] | None = None
    metadata: dict[str, str] | None = None

    def sample(self, *, axes=None, request=None):
        raise NotImplementedError

    def to_yaml_data(self) -> object:
        data = super().to_yaml_data()
        assert isinstance(data, dict)
        data["values"] = yaml_sequence(self.values, flow_style=True)
        data["bounds"] = yaml_sequence(self.bounds, flow_style=True)
        if self.labels:
            data["labels"] = yaml_sequence(self.labels, flow_style=True)
        if self.metadata:
            data["metadata"] = yaml_mapping(self.metadata, flow_style=True)
        return data
```

This keeps the module fields the same internally, but asks the YAML dumper to render those values inline:

```yaml
module: lookup
values: [0.1, 0.2, 0.3]
bounds: [0, 10]
shape: [age]
labels: [0-17, 18-64, 65+]
metadata: {kind: demo}
```

## 3. Keep Complex Structures Expanded

Flow style is usually best for short, simple values. For more complex nested data, developers can keep block style explicitly:

```python
from flepimop2.configuration import yaml_mapping, yaml_sequence
from flepimop2.parameter.abc import ParameterABC


class SeasonalParameter(ParameterABC, module="seasonal"):
    breakpoints: tuple[float, ...]
    segments: tuple[dict[str, float | str], ...]

    def sample(self, *, axes=None, request=None):
        raise NotImplementedError

    def to_yaml_data(self) -> object:
        data = super().to_yaml_data()
        assert isinstance(data, dict)
        data["breakpoints"] = yaml_sequence(self.breakpoints, flow_style=True)
        data["segments"] = yaml_sequence(
            (yaml_mapping(segment, flow_style=False) for segment in self.segments),
            flow_style=False,
        )
        return data
```

That combination keeps the simple `breakpoints` field compact while preserving a more readable block layout for the nested `segments` entries:

```yaml
module: seasonal
breakpoints: [0.0, 30.0, 60.0]
segments:
- start: 0.1
  end: 0.2
  mode: linear
- start: 0.2
  end: 0.15
  mode: hold
```

## 4. Guidelines

- Prefer overriding `to_yaml_data()` instead of changing `model_dump()` behavior. `patch()` logic still depends on the underlying model data, and mixing formatting rules into the patch representation can create surprising merge behavior.
- Use `yaml_sequence(..., flow_style=True)` or `yaml_mapping(..., flow_style=True)` for short values that are easier to scan inline.
- Keep nested or multi-entry structures in block style when readability matters more than compactness.
- Only change the user-facing shape when it improves clarity. The default serializer is already a reasonable baseline for many modules.

For runnable examples of both flow-style and block-style customization, see `tests/module/test_to_yaml_data.py` in the repository.
