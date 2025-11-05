# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Initialized `flepimop2`.
- Added `flepimop2` CLI and associated infrastructure, most of which is not public except the `flepimop2.logging` module.
- Added documentation using `mkdocs` that includes API/CLI reference as well as reusing `CHANGELOG.md` and `CONTRIBUTING.md` where appropriate.
- Added basic configuration models to parse and serialize configuration files. These are contained in the `flepimop2.configuration` module.
- Added core simulation infrastructure including engines (machinery to evolve a model) and systems (descriptions of model changes). These are contained in the `flepimop2.engine/system/backend` modules.
- Added the ability to execute auxiliary commands in the context of `flepimop2` with the `flepimop2 process` CLI backed by the `flepimop.process` module.
