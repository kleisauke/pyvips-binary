# pyvips-binary

[![Build status](https://github.com/kleisauke/pyvips-binary/actions/workflows/build-release.yml/badge.svg)](https://github.com/kleisauke/pyvips-binary/actions)
[![PyPI package](https://img.shields.io/pypi/v/pyvips-binary?label=PyPI%20package)](https://pypi.org/project/pyvips-binary/)

This binary package is an optional component of [pyvips](
https://github.com/libvips/pyvips), providing pre-built binary wheels for
running pyvips in [CFFI's API mode](
https://cffi.readthedocs.io/en/stable/overview.html#abi-versus-api) across
the most common platforms.

This package leverages the pre-compiled libvips binaries from
[this repository](https://github.com/kleisauke/libvips-packaging).
