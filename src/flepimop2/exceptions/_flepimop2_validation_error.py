from dataclasses import dataclass
from typing import Any

from flepimop2.exceptions._flepimop2_error import Flepimop2Error


@dataclass
class ValidationIssue:
    """
    Represents a single validation issue encountered during data validation.

    Attributes:
        msg: A human readable description of the validation issue.
        kind: The type/category of the validation issue.
        ctx: Optional context providing additional information about the issue.

    Examples:
        >>> from pprint import pprint
        >>> from flepimop2.exceptions import ValidationIssue
        >>> issue = ValidationIssue(
        ...     msg="Invalid wrapper data format.",
        ...     kind="invalid_format",
        ...     ctx={"expected_format": "JSON", "line": 42},
        ... )
        >>> pprint(issue)
        ValidationIssue(msg='Invalid wrapper data format.',
                        kind='invalid_format',
                        ctx={'expected_format': 'JSON', 'line': 42})
    """

    msg: str
    kind: str
    ctx: dict[str, Any] | None = None


class Flepimop2ValidationError(Flepimop2Error):
    """
    Exception raised for validation errors from `flepimop2`.

    This exception's main purpose is to signal that validation has failed
    within the `flepimop2` library and provides detailed information about
    the validation issues encountered, typically provided by an external
    provider package. The main benefit of this exception is to encapsulate
    multiple validation issues into a single error object, making it easier
    to handle and report validation failures as well as providing a consistent
    interface for validation errors across different parts of the `flepimop2`
    library.

    Attributes:
        issues: A list of `ValidationIssue` instances representing the validation
            errors.

    Examples:
        >>> from pprint import pprint
        >>> from flepimop2.exceptions import (
        ...     Flepimop2ValidationError,
        ...     ValidationIssue,
        ... )
        >>> issues = [
        ...     ValidationIssue(
        ...         msg="Model requires undefined parameter 'gamma'.",
        ...         kind="missing_parameter",
        ...         ctx={"parameter": "gamma", "transition": "gamma * (S / N)"},
        ...     ),
        ...     ValidationIssue(
        ...         msg="Compartment 'E' is unreachable.",
        ...         kind="unreachable_compartment",
        ...         ctx={"compartment": "E"},
        ...     ),
        ... ]
        >>> exception = Flepimop2ValidationError(issues)
        >>> pprint(exception.issues)
        [ValidationIssue(msg="Model requires undefined parameter 'gamma'.",
                         kind='missing_parameter',
                         ctx={'parameter': 'gamma', 'transition': 'gamma * (S / N)'}),
         ValidationIssue(msg="Compartment 'E' is unreachable.",
                         kind='unreachable_compartment',
                         ctx={'compartment': 'E'})]
        >>> print(exception)
        2 validation issues encountered:
        - [missing_parameter] Model requires undefined parameter 'gamma'. (parameter=gamma, transition=gamma * (S / N))
        - [unreachable_compartment] Compartment 'E' is unreachable. (compartment=E)
        >>> raise Flepimop2ValidationError(issues)
        Traceback (most recent call last):
            ...
        flepimop2.exceptions.Flepimop2ValidationError: 2 validation issues encountered:
        - [missing_parameter] Model requires undefined parameter 'gamma'. (parameter=gamma, transition=gamma * (S / N))
        - [unreachable_compartment] Compartment 'E' is unreachable. (compartment=E)


    """  # noqa: E501

    def __init__(self, issues: list[ValidationIssue]) -> None:
        """
        Initialize the Flepimop2ValidationError.

        Args:
            issues: A list of `ValidationIssue` instances representing the validation
                errors.
        """
        self.issues = issues
        message = self._format_issues(issues)
        super().__init__(message)

    @staticmethod
    def _format_issues(issues: list[ValidationIssue]) -> str:
        """
        Format validation issues into a readable error message.

        Args:
            issues: A list of `ValidationIssue` instances to format.

        Returns:
            A formatted string representation of all validation issues.

        Examples:
            >>> from flepimop2.exceptions import (
            ...     ValidationIssue,
            ...     Flepimop2ValidationError,
            ... )
            >>> issues = [
            ...     ValidationIssue(
            ...         msg="Missing required field 'model'.",
            ...         kind="missing_field",
            ...         ctx={"field": "model"},
            ...     ),
            ...     ValidationIssue(
            ...         msg="Invalid value for 'dt'.",
            ...         kind="invalid_value",
            ...         ctx={"field": "dt", "value": -5},
            ...     ),
            ... ]
            >>> print(Flepimop2ValidationError._format_issues(issues))
            2 validation issues encountered:
            - [missing_field] Missing required field 'model'. (field=model)
            - [invalid_value] Invalid value for 'dt'. (field=dt, value=-5)
            >>> issues = [
            ...     ValidationIssue(
            ...         msg="Model outputs are not guaranteed to be non-negative.",
            ...         kind="negative_output_warning",
            ...     ),
            ... ]
            >>> print(Flepimop2ValidationError._format_issues(issues))
            1 validation issue encountered:
            - [negative_output_warning] Model outputs are not guaranteed to be non-negative.

        """  # noqa: E501
        count = len(issues)
        plural = "issue" if count == 1 else "issues"
        lines = [f"{count} validation {plural} encountered:"]

        for issue in issues:
            # Start with the kind and message
            line = f"- [{issue.kind}] {issue.msg}"

            # Add context if present
            if issue.ctx:
                ctx_parts = [f"{k}={v}" for k, v in issue.ctx.items()]
                line += f" ({', '.join(ctx_parts)})"

            lines.append(line)

        return "\n".join(lines)
