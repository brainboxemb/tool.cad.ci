# CAD-CI command-line adapter

This package is the public `cad-ci` command-line entry point, not the CAD-CI execution engine. See [API inventory](../docs/api.md) and [consumer guide](../docs/consumer.md).

| Module | Responsibility |
| --- | --- |
| `cli.py` | CLI entry point, planning/running argument parsing, output and error handling |
| `publication_cli.py` | Build-scope and generated-branch publication command exposure |
| `__main__.py` | `python -m cad_ci_tool` entry point |
| `__init__.py` | Python package marker |

Behavior for selection, SCons execution, build-store membership and Pages publication is implemented by the exact pinned `lib.py.cad.ci` revision. Do not duplicate it in this directory.

The full public CLI options, error contracts and traceability are being audited under [issue #110](https://github.com/brainboxemb/tool.cad.ci/issues/110). Until then, this README describes ownership, **not** approval of every currently supported flag. CLI changes require unit tests and acceptance of the exact released stack in `tool.cad.ci.test`.
