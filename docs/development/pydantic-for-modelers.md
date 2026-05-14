# Pydantic for Modelers

All `flepimop2` module classes (`BackendABC`, `EngineABC`, `SystemABC`, etc.) inherit from `ModuleBase`, which is a `pydantic.BaseModel`. This gives you configuration parsing, type coercion, and validation for free. This guide covers the parts of `pydantic` most relevant to writing `flepimop2` modules - see the [`pydantic` v2 docs](https://docs.pydantic.dev/latest/) for everything else.

## Fields

Declare fields as class-level annotations. `pydantic` handles coercion (e.g. `str → Path`) and validation automatically:

```python
from pathlib import Path
from pydantic import Field
from flepimop2.backend.abc import BackendABC


class NpzBackend(BackendABC, module="npz"):
    root: Path = Field(default_factory=lambda: Path.cwd() / "output")
    compressed: bool = True
```

Use `@field_validator` and `@model_validator` for custom validation logic. See the [`pydantic` validators docs](https://docs.pydantic.dev/latest/concepts/validators/) for details.

## The `module=` Class Keyword

Every concrete module class must declare its identity for `flepimop2` to locate it when a user specifies a `module:` in configuration. This is done via the `module=` class keyword argument:

```python
# resolves to "flepimop2.backend.npz"
class NpzBackend(BackendABC, module="npz"):
    ...
```

Short names are resolved against the ABC's namespace. Fully-qualified names pass through unchanged. This sets the `module` field to a `Literal` constrained to that exact value - any config that passes the wrong `module:` string raises a `ValidationError`.

## Private Attributes and `model_post_init`

Use `PrivateAttr` to specify instance state that isn't a configuration field (runtime callables, caches, loaded resources). Wire them up in `model_post_init`, which runs after all fields are validated:

```python
from typing import Any
from pydantic import PrivateAttr
from flepimop2.engine.abc import EngineABC


def _my_runner(*args, **kwargs):
    pass


class MyEngine(EngineABC, module="myengine"):
    _runner: Any = PrivateAttr(default=None)

    def model_post_init(self, context: Any) -> None:
        super().model_post_init(context)
        self._runner = _my_runner
```

Always call `super().model_post_init(context)` first so that parent-class initialization runs.

If you pass a callable directly as `PrivateAttr(default=my_func)`, Python's descriptor protocol will bind `my_func` to the instance when you access `self._runner`, turning it into a bound method that receives `self` as its first argument. Always use `PrivateAttr(default=None)` and assign the callable in `model_post_init` instead - that assignment path does not trigger binding.

## The `options` Grab-Bag

`ModuleBase` provides an `options` field for arbitrary key-value metadata that doesn't belong in the typed schema. Users can set it in config:

```yaml
system:
  module: sir
  state_change: flow
  options:
    description: "Basic SIR model"
```

These values can be accessed via [`ModuleBase.option`](./../reference/api/module.md#flepimop2.module.ModuleBase.option).

## Leveraging Third-Party Input Validation

If you are wrapping an existing library that has its own validation, the quickest way to integrate it is a `mode="after"` model validator that dumps the fields to a dict, then pass the relevant values to your library's validator.

<!-- skip: start -->
```python
from typing import Self
from pydantic import model_validator
from flepimop2.system.abc import SystemABC
from mylib import MyLibConfig  # your library's validator


class MySystem(SystemABC, module="mysystem"):
    state_change: StateChangeEnum = StateChangeEnum.FLOW
    tolerance: float = 1e-6
    max_iter: int = 1000

    @model_validator(mode="after")
    def _validate_with_mylib(self) -> Self:
        config = self.model_dump()
        MyLibConfig(tolerance=config["tolerance"], max_iter=config["max_iter"])
        return self
```
<!-- skip: end -->

The validator call raises on bad input and `flepimop2` surfaces the error before any simulation runs.

However, this approach is quick but not the most user-friendly - validation errors come from your library's types rather than from `flepimop2`'s schema, which can be confusing. If your library already exposes `pydantic` models, the better path is to embed them directly as fields in your module class. That way the configuration structure mirrors the library's own interface and users get native `pydantic.ValidationError` messages that reference the exact field that failed.

## Further Reading

- [Pydantic v2 documentation](https://docs.pydantic.dev/latest/)
- [Creating an External Provider Package](./creating-an-external-provider-package.md)
- [Implementing Custom Engines and Systems](./implementing-custom-engines-and-systems.md)
