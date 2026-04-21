# Installation

`flepimop2` is published on [PyPI](https://pypi.org/project/flepimop2/) and can be installed with `pip`:

```bash
pip install flepimop2
```

If you use `uv`, you can install it into the current environment with:

```bash
uv pip install flepimop2
```

## Add It To A Project

If you want `flepimop2` to be a dependency of another Python project, add it to that project’s dependency list.

With `uv`, the simplest option is:

```bash
uv add flepimop2
```

If you manage dependencies manually in `pyproject.toml`, add the package name to `project.dependencies`:

```toml
[project]
dependencies = [
    "flepimop2",
]
```

After installation, the `flepimop2` CLI should be available in your environment:

```bash
flepimop2 --help
```

## Installing From GitHub

`flepimop2` is still in the alpha/beta development stage and you may find that newer features are available with the development version. In this case you can install `flepimop2` directly from GitHub via:

```bash
pip install git+https://github.com/ACCIDDA/flepimop2.git@main
```

If you use `uv`, you can install it into the current environment with:

```bash
uv pip install git+https://github.com/ACCIDDA/flepimop2.git@main
```

The `@main` indicates to install from the main branch, but you can also change this to install from a specific branch or tag.
