<!-- skip: start -->
# Adding A New CLI Command

This tutorial will show how to:

- Add a new command to the `flepimop2` CLI.
- Add a new option to `flepimop2`'s CLI infrastructure.
- Test the newly added command.

In this tutorial will demonstrate adding a new command called `flepimop2 hello` which will print hello world a user specified number of times.

## Brief Overview Of `flepimop2`'s CLI Infrastructure

`flepimop2`'s CLI infrastructure might be a bit heavier and stricter than previous CLI programs a developer has worked with. The reason for this is to enforce consistency for the inputs and outputs of CLI commands. The primary restrictions of this approach are:

- CLI commands must implement a common abstract base class which provides a common framework for command implementations.
- Options/arguments are shared among all CLI commands so they have the same meaning and usage across commands. Developers cannot add bespoke options/arguments for their command.
- CLI outputs are made consistent via a common logging infrastructure so the outputs of commands have a common feel across the `flepimop2` CLI.

`flepimop2`'s CLI infrastructure is contained in the private `flepimop2._cli` subpackage. The most important elements of this subpackage are:

- `CliCommand`: The abstract base class that CLI commands must implement. The main benefit of having CLI commands subclass a common class is that repeated logic can be consolidated, CLI inputs/outputs can be made consistent, and development work can be eased.
- `COMMON_OPTIONS`: A constant dictionary mapping option/argument names to their definitions. CLI commands can request options/arguments from this dictionary by having them as keyword only arguments to their `run` method. The main benefit of this approach is that commands cannot define bespoke options/arguments and developers are forced to use consistent meanings across commands. I.e. the `--dry-run` option means the same thing in all commands.
- `register_command`: The function that attaches a user's implementation of `CliCommand` to the `flepimop2` CLI.

This infrastructure utilizes [`click`](https://click.palletsprojects.com/en/stable/) so it may be helpful to reference their documentation occasionally. 

## Adding The `flepimop2 hello` Command

In particular this tutorial will be add a new command to the `flepimop2` CLI called `hello` which will take a new number argument. The end result of this tutorial will be:

```shell
$ flepimop2 --help
Usage: flepimop2 [OPTIONS] COMMAND [ARGS]...

  flepimop2 - Flexible Epidemic Modeling Pipeline (version 2).

Options:
  --version  Show the version and exit.
  --help     Show this message and exit.

Commands:
  build     Compile and build a model defined in a configuration file.
  hello     This command says hello a specified number of times.
  process   Execute a processing step based on a configuration file.
  simulate  Run simulations based on a configuration file.
$ flepimop2 hello --help
Usage: flepimop2 hello [OPTIONS] [TIMES]

  This command says hello a specified number of times.

Options:
  --dry-run        Should this command be run using dry run?
  -v, --verbosity  The verbosity level to use for this command.
  --help           Show this message and exit.
```

### Add The `HelloCommand` Class

The first step is to implement the `HelloCommand` class in a new `src/flepimop2/_cli/_hello_command.py` file.

```python
"""Hello command implementation."""

__all__ = []


from flepimop2._cli._cli_command import CliCommand


class HelloCommand(CliCommand):
    """This command says hello a specified number of times."""

    def run(self, *, times: int, dry_run: bool) -> None:  # type: ignore[override]
        """
        Say hello a specified number of times.

        Args:
            times: The number of times to say hello.
            dry_run: Whether dry run mode is enabled.
        """
        if dry_run:
            self.info(f"Would said hello {times} time(s).")
            return
        for i in range(times):
            self.info(f"({i + 1}/{times}) Hello, world!")
```

The `run` method contains the logic of the command and it's keyword arguments correspond to the options/arguments requested from `COMMON_OPTIONS`. The `CliCommand` also provides consistent logging infrastructure in the form of the `log`, `debug`, `info`, `warning`, `error`, and `critical` methods. Note that a `verbosity` option is not explicitly requested, this option is added by default to the command and `CliCommand` handles translating the given verbosity to a logging level so developers only need to concern themselves with calling the appropriate logging method. To ease development the class docstring will be used as the help string for the command and the command's name is extracted from the class name.

### Adding A New Option

The implementation of `flepimop2 hello` needs a times argument. To add this argument a developer needs to add it to the `COMMON_OPTIONS` dictionary in `src/flepimop2/_cli/_options.py`.

```python
# Dictionary of common Click options and arguments
# These can be requested by command classes to maintain consistency
COMMON_OPTIONS: Final = {
    ...
    "times": click.argument(
        "times",
        type=click.IntRange(min=1),
        default=1,
        required=False,
    ),
    ...
}
```

This adds a new `times` argument to the `COMMON_OPTIONS` dictionary. Note that the argument is not tied specifically to the `flepimop2 hello` command since this argument could be used by other commands.

### Register The New Command

The final step is to register the new command with the `flepimop2` CLI by adding a call to `register_command` in `src/flepimop2/_cli/_cli.py`.

```python
...
from flepimop2._cli._build_command import BuildCommand
from flepimop2._cli._hello_command import HelloCommand
from flepimop2._cli._process_command import ProcessCommand
...
# Register all commands
register_command(BuildCommand, cli)
register_command(SimulateCommand, cli)
register_command(ProcessCommand, cli)
register_command(HelloCommand, cli)
```

The `register_command` function takes the CLI command class as it's first argument and the [`click.Group`](https://click.palletsprojects.com/en/stable/api/#click.Group) to attach the command to. In this case the command is being attached to the main cli, `cli`, so it can be invoked `flepimop2 hello`. But one could have created a new click group so one could have nested subcommands, i.e. `flepimop2 greetings hello`.

## Testing A New Command

Before preparing this command for a PR it's important to test the new command. There are two types of testing:

1. Ad-hoc testing: Testing the command manually for expected behavior.
2. Unit testing: Programmatically testing the command.

### Ad-Hoc Testing

The first pass for testing a new command should be ad-hoc testing because it's the easiest way to get feedback during development. This entails running the command several times and manually checking that the output matches the expected.

```shell
$ flepimop2 hello --help
Usage: flepimop2 hello [OPTIONS] [TIMES]

  This command says hello a specified number of times.

Options:
  --dry-run        Should this command be run using dry run?
  -v, --verbosity  The verbosity level to use for this command.
  --help           Show this message and exit.
$ flepimop2 hello 3
$ flepimop2 hello -v 3
$ flepimop2 hello -vv 3
2025-11-06 09:48:40,962:INFO> (1/3) Hello, world!
2025-11-06 09:48:40,962:INFO> (2/3) Hello, world!
2025-11-06 09:48:40,962:INFO> (3/3) Hello, world!
$ flepimop2 hello -vvv 3
2025-11-06 09:48:46,452:DEBUG> Given 2 options/arguments:
2025-11-06 09:48:46,452:DEBUG> times   = 3.
2025-11-06 09:48:46,452:DEBUG> dry_run = 0.
2025-11-06 09:48:46,452:INFO> (1/3) Hello, world!
2025-11-06 09:48:46,452:INFO> (2/3) Hello, world!
2025-11-06 09:48:46,452:INFO> (3/3) Hello, world!
$ flepimop2 hello -vv --dry-run 5
2025-11-06 09:49:00,106:INFO> Would said hello 5 time(s).
$ flepimop2 hello 0
Usage: flepimop2 hello [OPTIONS] [TIMES]
Try 'flepimop2 hello --help' for help.

Error: Invalid value for '[TIMES]': 0 is not in the range x>=1.
```

This quick ad-hoc testing matches the following expected behavior:

- The command should only produce output at `-vv` and above because it uses the `info` method to log output.
- The command says "Hello, world!" the number of times given.
- Providing `--dry-run` does not repeat the greeting, but instead says it would have done so.
- Providing 0 or less for times results in an error that is caught before the command can run.

### Unit Testing

Ad-hoc testing is great for development purposes or diagnosing bugs quickly, but is not sustainable for long term maintenance. However, writing unit tests for CLI commands can be especially tricky because much of what CLI commands do is glue together behavior from other objects and emit output. Before unit testing a CLI command a developer should ask the following:

1. Can this behavior and corresponding unit test be pushed down to the object being operated on or a new function? For example, suppose that `flepimop2 hello` worked with the `RunMeta` object and formatted the timestamp for display. In this case the formatting behavior should be added to the `RunMeta` object and tested there instead of testing that behavior via `HelloCommand`.
2. Is the behavior essential to the CLI command? For example, the output logged to the user is non-essential. `flepimop2` does not make guarantees about CLI output consistency across versions. The only case where one might want to test the logged output is to see if a particular branch was reached, i.e. a certain message is only emitted if certain conditions are met.

With that being said, the `flepimop2 hello` command does not have behavior that would be worth unit testing. For the purposes of unit testing change the `HelloCommand.run` method to:

```python
...
    def run(self, *, times: int, dry_run: bool) -> None:  # type: ignore[override]
        """
        Say hello a specified number of times.

        Args:
            times: The number of times to say hello.
            dry_run: Whether dry run mode is enabled.
        
        Raises:
            ValueError: If `times` is greater than 10.
        """
        if times > 10:
            msg = "Cannot say hello more than 10 times."
            raise ValueError(msg)
        if dry_run:
            self.info(f"Would said hello {times} time(s).")
            return
        for i in range(times):
            self.info(f"({i + 1}/{times}) Hello, world!")
```

Now the command has behavior, raising an exception, that is worth testing and cannot be pushed to the object being operated on or an external function. To unit test this behavior add the following to `tests/_cli/test_hello_command.py`:

```python
"""Unit tests for the `flepimop2 hello` CLI command."""

from flepimop2._cli._hello_command import HelloCommand
import pytest


def test_raises_value_error_if_times_exceeds_limit() -> None:
    """Test that ValueError is raised if times > 10."""
    command = HelloCommand()
    with pytest.raises(ValueError, match=r"Cannot say hello more than 10 times."):
        command.run(times=11, dry_run=False)
```

Another benefit to `flepimop2`'s CLI infrastructure is that the `run` method of a `CliCommand` subclass can be tested directly rather than needing to use [`subprocess.run`](https://docs.python.org/3/library/subprocess.html#subprocess.run) or [`click.testing.CliRunner`](https://click.palletsprojects.com/en/stable/testing/). If the verbosity level needs to be controlled for a unit test a developer could modify this test by invoking `HelloCommand.__call__` instead with the same arguments as `run` but including verbosity like so:

```python
"""Unit tests for the `flepimop2 hello` CLI command."""

from flepimop2._cli._hello_command import HelloCommand
import pytest


def test_raises_value_error_if_times_exceeds_limit() -> None:
    """Test that ValueError is raised if times > 10."""
    command = HelloCommand()
    with pytest.raises(ValueError, match=r"Cannot say hello more than 10 times."):
        command(times=11, dry_run=False, verbosity=0)
```

## Summary

This tutorial covered:

- A high level overview of the `flepimop2` CLI infrastructure.
- Adding a new command to the `flepimop2` CLI.
- Adding a new option to `flepimop2`'s CLI infrastructure.
- Testing the newly added command.

<!-- skip: end -->
