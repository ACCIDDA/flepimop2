# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Initialized `flepimop2`.
- Added documentation using `mkdocs` that includes API/CLI reference as well as reusing `CHANGELOG.md` and `CONTRIBUTING.md` where appropriate.
- Added basic configuration models to parse and serialize configuration files. These are contained in the `flepimop2.configuration` module.
- Added core simulation infrastructure including engines (machinery to evolve a model) and systems (descriptions of model changes). These are contained in the `flepimop2.engine/system/backend` modules.
- Added the ability to execute auxiliary commands in the context of `flepimop2` with the `flepimop2 process` CLI backed by the `flepimop.process` module.
- Converted `flepimop2` to a PEP420 implicit namespace package so external providers can inject themselves into the `flepimop2` namespace. This allows users to reference modules by name only and then `flepimop2` will resolve the kind of module based on its location in a configuration file. See [#45](https://github.com/ACCIDDA/flepimop2/issues/45).
- Added `flepimop2.abcs` as a convenient re-export of ABCs/protocols for developer use. See [#85](https://github.com/ACCIDDA/flepimop2/issues/85).
- Made parameters modular, similar to backends/engines/processes/systems, to allow external packages to provide their own parameter types. See [#75](https://github.com/ACCIDDA/flepimop2/issues/75).
- Restricted the name of user defined backends/engines/parameters/processes/systems to comply with the custom `IdentifierString` type.
- Added a new `flepimop2 skeleton` CLI command for scaffolding a project repository. See [#84](https://github.com/ACCIDDA/flepimop2/issues/84).
- Added `flepimop.testing` with functionality for integration testing, both for `flepimop2` itself and for external provider packages. See [#107](https://github.com/ACCIDDA/flepimop2/issues/107).
