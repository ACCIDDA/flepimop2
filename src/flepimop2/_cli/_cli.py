__all__ = []


import click

from flepimop2 import __version__
from flepimop2._cli._build_command import BuildCommand
from flepimop2._cli._process_command import ProcessCommand
from flepimop2._cli._register_command import register_command
from flepimop2._cli._simulate_command import SimulateCommand


@click.group()
@click.version_option(version=__version__)
def cli() -> None:
    """flepimop2 - Flexible Epidemic Modeling Pipeline (version 2)."""


# Register all commands
register_command(BuildCommand, cli)
register_command(SimulateCommand, cli)
register_command(ProcessCommand, cli)
