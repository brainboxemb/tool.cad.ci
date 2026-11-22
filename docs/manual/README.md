# Consumer documentation

This directory is the user-facing documentation area for repositories that
consume `tool.cad.ci`.

- [manual.md](manual.md) — setup, template selection, allowed customization and
  verification guidance.
- [templates/](templates/) — copy-ready, versioned GitHub Actions workflow
  templates.

The templates are deliberately kept in their own directory. Do not place YAML
templates beside the Markdown manual files.

Current copy-ready baseline: `tool.cad.ci 0.23.0` at
`bc0a7b716f67a20e63eaf8b89a2c35c381fb8bf1`.

Start with [manual.md](manual.md); do not design generic CAD-CI orchestration
from scratch in a consumer repository.
