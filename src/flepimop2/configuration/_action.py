from datetime import UTC, datetime

from pydantic import BaseModel, Field


class ActionModel(BaseModel):
    """
    Action model for flepimop2 configuration history and run metadata.

    This model serves as both the metadata for individual runs and as entries
    in the configuration history.

    Attributes:
        action: The action performed in the run (e.g., "simulate", "process").
        timestamp: The timestamp when the run was executed.
        name: An optional name for the run, typically pulled from the config.

    Examples:
        >>> from flepimop2.configuration._action import ActionModel
        >>> action = ActionModel(action="simulate", name="test_run")
        >>> action.action
        'simulate'
        >>> action.name
        'test_run'
    """

    action: str = Field(min_length=1, default="simulate")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    name: str | None = None
