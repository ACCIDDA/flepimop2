"""Unit tests for the `BackendABC` save-context forwarding."""

import numpy as np

from flepimop2.backend.abc import BackendABC
from flepimop2.meta import RunMeta
from flepimop2.parameter.abc import ModelStateSpecification
from flepimop2.typing import Float64NDArray


def test_backend_save_does_not_forward_context_to_unaware_backend() -> None:
    """A `_save` without model_state/axes params never receives them."""
    received: dict[str, object] = {}

    class _LegacyBackend(BackendABC, module="flepimop2.test.legacy_backend"):
        def _save(self, data: object, run_meta: RunMeta) -> None:  # noqa: ARG002
            received["called"] = True

        def _read(self, run_meta: RunMeta) -> Float64NDArray:  # noqa: ARG002
            return np.array([])

    backend = _LegacyBackend()
    model_state = ModelStateSpecification(parameter_names=("s0",))
    backend.save(np.array([[1.0]]), RunMeta(), model_state=model_state)

    assert received == {"called": True}
