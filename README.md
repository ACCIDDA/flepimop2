# `flepimop2`: *FLE*xible *P*ipeline for *I*nterchangeable *MO*del *P*rocessing

[![DOI](https://zenodo.org/badge/1072205034.svg)](https://zenodo.org/badge/latestdoi/1072205034)

`flepimop2` is a Python package and command-line tool for running dynamical system simulations from configuration files. Separate providers define the mathematical model (system), numerical solver (engine), and result storage (backend). Other interfaces cover parameters, processing steps, and job execution. Projects can use the library directly or add providers for their own models and analyses.

To learn more and try out the tool, see the [documentation](https://accidda.github.io/flepimop2/latest/).

## Installation

`flepimop2` is published on [PyPI](https://pypi.org/project/flepimop2/) and can be installed with:

```bash
pip install flepimop2
```

If you are adding `flepimop2` as a dependency in another project, see the [installation guide](docs/guides/install.md).

## Contributing

Contributions are welcomed and appreciated! Please see the [contributing guide](CONTRIBUTING.md) for details on development setup, code standards, testing, and the pull request process.

## Funding Acknowledgement

This project was made possible by the Insight Net cooperative agreement CDC-RFA-FT-23-0069 from the CDC’s Center for Forecasting and Outbreak Analytics. Its contents are solely the responsibility of the authors and do not necessarily represent the official views of the Centers for Disease Control and Prevention.
