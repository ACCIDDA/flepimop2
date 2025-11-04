"""Tests for the `register_command` function in `flepimop2._cli._cli`."""

from unittest.mock import MagicMock

import click
import pytest
from click.testing import CliRunner

from flepimop2._cli._cli_command import CliCommand
from flepimop2._cli._register_command import register_command


class MockCommand(CliCommand):
    """Mock command for testing."""

    def run(self, *, dry_run: bool) -> None:  # type: ignore[override]
        """Mock run method."""
        click.echo(f"Mock command ran with: {{'dry_run': {dry_run}}}")


class MockCommandNoOptions(CliCommand):
    """Mock command with no options for testing."""

    def run(self) -> None:  # type: ignore[override]
        """Mock run method with no options."""
        click.echo("Mock command with no options ran")


class MockCommandCustomName(CliCommand):
    """Mock command with custom name."""

    @classmethod
    def command_name(cls) -> str:
        """
        Override command name.

        Returns:
            The custom command name to use in the CLI.
        """
        return "custom-name"

    def run(self) -> None:  # type: ignore[override]
        """Mock run method."""
        click.echo("Custom named command ran")


class MockCommandCustomHelp(CliCommand):
    """Mock command with custom help text."""

    @classmethod
    def help_text(cls) -> str:
        """
        Override help text.

        Returns:
            The custom help text for this command.
        """
        return "Custom help text for this command."

    def run(self) -> None:  # type: ignore[override]
        """Mock run method."""
        click.echo("Custom help command ran")


class MockCommandWithOverriddenOptions(CliCommand):
    """Mock command that overrides the options() method."""

    @classmethod
    def options(cls) -> list[str]:
        """Override to provide custom options different from run parameters.

        Returns:
            Tuple of option names to request.
        """
        return ["verbosity"]  # Only verbosity, not extra_param

    def run(self, *, verbosity: int, extra_param: str = "default") -> None:  # type: ignore[override]
        """
        Mock run method with different parameters.

        Note: extra_param has a default and won't be in options().
        """
        click.echo(f"Command ran with verbosity: {verbosity}, extra: {extra_param}")


class MockCommandNoAutoVerbosity(CliCommand):
    """Mock command that disables auto-appending verbosity."""

    auto_append_verbosity = False

    def run(self, *, config: str) -> None:  # type: ignore[override]
        """Mock run method."""
        click.echo(f"Command ran with config: {config}")


class MockCommandWithNonExistentOption(CliCommand):
    """Mock command that requests a non-existent option."""

    def run(self, *, non_existent_option: str) -> None:  # type: ignore[override]
        """Mock run method."""
        click.echo(
            f"This should not run due to non-existent option, {non_existent_option}."
        )


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

    # Options should be applied in order: dry_run, then verbosity (auto-appended)
    param_names = [param.name for param in test_cli.commands["mock"].params]
    assert param_names == MockCommand.options() == ["dry_run", "verbosity"]


def test_register_command_with_no_options() -> None:
    """Test that register_command works with commands that have no options."""
    test_cli = click.Group()

    register_command(MockCommandNoOptions, test_cli)

    command = test_cli.commands["mock-command-no-options"]

    # Should only have verbosity parameter (auto-appended)
    assert len(command.params) == 1
    assert command.params[0].name == "verbosity"


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
    mock_command_cls.options.return_value = ()

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


def test_register_command_allows_custom_options_override() -> None:
    """Test that commands can override options() for custom behavior."""
    test_cli = click.Group()

    register_command(MockCommandWithOverriddenOptions, test_cli)

    command = test_cli.commands["mock-command-with-overridden-options"]

    # Should only have verbosity parameter, not dry_run or extra_param
    param_names = [param.name for param in command.params]
    assert param_names == ["verbosity"]
    assert "dry_run" not in param_names
    assert "extra_param" not in param_names


def test_introspection_gets_keyword_only_params() -> None:
    """Test that options introspection correctly identifies keyword-only params."""
    # MockCommand should automatically introspect dry_run and auto-append verbosity
    options = MockCommand.options()
    assert options == ["dry_run", "verbosity"]

    # MockCommandNoOptions should only have verbosity (auto-appended)
    options_no_params = MockCommandNoOptions.options()
    assert options_no_params == ["verbosity"]


def test_auto_append_verbosity_can_be_disabled() -> None:
    """Test that auto_append_verbosity can be set to False to disable auto-appending."""
    # Command with auto_append_verbosity = False should not have verbosity
    options = MockCommandNoAutoVerbosity.options()
    assert options == ["config"]
    assert "verbosity" not in options


def test_non_existent_option_raises_key_error() -> None:
    """Test that requesting a non-existent option raises KeyError."""
    with pytest.raises(
        KeyError,
        match=r"Unknown option 'non_existent_option'. Available options: .*",
    ):
        register_command(MockCommandWithNonExistentOption, click.Group())
