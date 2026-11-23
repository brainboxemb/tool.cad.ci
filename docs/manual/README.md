# Consumer documentation

This directory is the user-facing documentation area for repositories that
consume `tool.cad.ci`.

- [manual.md](manual.md) — setup, template selection, allowed customization and
  verification guidance.
- [templates/](templates/) — copy-ready, versioned GitHub Actions workflow
  templates.

The templates are deliberately kept in their own directory. Do not place YAML
templates beside the Markdown manual files.

Current copy-ready baseline: `tool.cad.ci v0.36.0`.

Start with [manual.md](manual.md); do not design generic CAD-CI orchestration
from scratch in a consumer repository.
