# flepimop2: The FLExible Pipeline for Interchangeable MOdel Processing
# Copyright (C) 2026  Carl Pearson, Joshua Macdonald, Timothy Willard
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
__all__ = []


import click

from flepimop2._cli._build_command import BuildCommand
from flepimop2._cli._process_command import ProcessCommand
from flepimop2._cli._register_command import register_command
from flepimop2._cli._simulate_command import SimulateCommand
from flepimop2._cli._skeleton_command import SkeletonCommand


@click.group()
@click.version_option(
    version="0.1.0",
    message="%(prog)s %(version)s\nLicense: GNU GPL v3 <https://www.gnu.org/licenses/>",
)
def cli() -> None:
    """flepimop2 - Flexible Epidemic Modeling Pipeline (version 2)."""


# Register all commands
register_command(BuildCommand, cli)
register_command(SimulateCommand, cli)
register_command(ProcessCommand, cli)
register_command(SkeletonCommand, cli)
