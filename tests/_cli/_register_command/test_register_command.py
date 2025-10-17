"""Tests for the `register_command` function in `flepimop2._cli._cli`."""

from typing import Any
from unittest.mock import MagicMock

import click
from click.testing import CliRunner

from flepimop2._cli._cli_command import CliCommand
from flepimop2._cli._register_command import register_command


class MockCommand(CliCommand):
    """Mock command for testing."""

    options = ("verbosity", "dry_run")

    @staticmethod
    def run(**kwargs: Any) -> None:
        """Mock run method."""
        click.echo(f"Mock command ran with: {kwargs}")


class MockCommandNoOptions(CliCommand):
    """Mock command with no options for testing."""

    options = ()

    @staticmethod
    def run(**kwargs: Any) -> None:  # noqa: ARG004
        """Mock run method with no options."""
        click.echo("Mock command with no options ran")


class MockCommandCustomName(CliCommand):
    """Mock command with custom name."""

    options = ("verbosity",)

    @classmethod
    def command_name(cls) -> str:
        """
        Override command name.

        Returns:
            The custom command name to use in the CLI.
        """
        return "custom-name"

    @staticmethod
    def run(**kwargs: Any) -> None:  # noqa: ARG004
        """Mock run method."""
        click.echo("Custom named command ran")


class MockCommandCustomHelp(CliCommand):
    """Mock command with custom help text."""

    options = ()

    @classmethod
    def help_text(cls) -> str:
        """
        Override help text.

        Returns:
            The custom help text for this command.
        """
        return "Custom help text for this command."

    @staticmethod
    def run(**kwargs: Any) -> None:  # noqa: ARG004
        """Mock run method."""
        click.echo("Custom help command ran")


def test_register_command_creates_click_command() -> None:
    """Test that register_command creates and registers a Click command."""
    # Create a fresh CLI group for testing
    test_cli = click.Group()

    register_command(MockCommand, test_cli)

    # Verify the command was registered
    assert "mock" in test_cli.commands
    assert isinstance(test_cli.commands["mock"], click.Command)


def test_register_command_uses_custom_command_name() -> None:
    """Test that register_command respects custom command names."""
    test_cli = click.Group()

    register_command(MockCommandCustomName, test_cli)

    # Should use the custom name
    assert "custom-name" in test_cli.commands


def test_register_command_applies_options_in_correct_order() -> None:
    """Test that options are applied in the correct order."""
    test_cli = click.Group()

    register_command(MockCommand, test_cli)

    # Options should be applied in order: config (argument), then verbosity
    param_names = [param.name for param in test_cli.commands["mock"].params]
    assert param_names == list(MockCommand.options)


def test_register_command_with_no_options() -> None:
    """Test that register_command works with commands that have no options."""
    test_cli = click.Group()

    register_command(MockCommandNoOptions, test_cli)

    command = test_cli.commands["mock-command-no-options"]

    # Should have no parameters
    assert len(command.params) == 0


def test_register_command_sets_help_text() -> None:
    """Test that register_command sets the help text from docstring."""
    test_cli = click.Group()
    register_command(MockCommand, test_cli)

    command = test_cli.commands["mock"]

    # Help text should come from the class docstring
    assert command.help == (MockCommand.__doc__ or "No description available.").strip()


def test_register_command_uses_custom_help_text() -> None:
    """Test that register_command respects custom help text."""
    test_cli = click.Group()
    register_command(MockCommandCustomHelp, test_cli)

    command = test_cli.commands["mock-command-custom-help"]

    # Should use the custom help text
    assert command.help == "Custom help text for this command."


def test_register_command_wrapper_instantiates_and_runs() -> None:
    """Test that the command wrapper instantiates the command and calls run."""
    test_cli = click.Group()

    # Mock the command class
    mock_instance = MagicMock()
    mock_command_cls = MagicMock(spec=CliCommand)
    mock_command_cls.return_value = mock_instance
    mock_command_cls.command_name.return_value = "test-cmd"
    mock_command_cls.help_text.return_value = "Test help"
    mock_command_cls.options = ()

    register_command(mock_command_cls, test_cli)

    # Get the registered command
    command = test_cli.commands["test-cmd"]

    # Invoke the command
    runner = CliRunner()
    runner.invoke(command, [])

    # Verify the command was instantiated and run was called
    mock_command_cls.assert_called_once()
    mock_instance.assert_called_once()


def test_register_command_passes_kwargs_to_run() -> None:
    """Test that command arguments are passed to the run method."""
    test_cli = click.Group()

    register_command(MockCommand, test_cli)

    command = test_cli.commands["mock"]

    # Invoke with arguments
    runner = CliRunner()
    result = runner.invoke(command, ["-vvv", "--dry-run"])

    # Check that the command ran successfully
    assert result.exit_code == 0
    assert "verbosity" in result.output or "Mock command ran" in result.output
