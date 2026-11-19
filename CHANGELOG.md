# Changelog

## 0.3.0 - 2026-11-19

- split reusable Python CI mechanics into `lib.py.cad.ci`;
- reduce `tool.cad.ci` to the CLI adapter that pins the library by exact commit;
- consume `lib.py.cad.ci` v0.1.2 for direct fan-in selection and validated dependency context.

## 0.2.2 - 2026-11-18

- add `cad-ci build update-main` for partial main baseline updates;
- validate all selected replacement items before writing the new candidate;
- preserve every unselected baseline item and manifest row;
- allow selected new catalog items to be added without a full rebuild.

## 0.2.1 - 2026-11-18

- allow a step output to be a directory as well as a file;
- hash directory contents recursively in stable relative-path order;
- invalidate reuse when a nested output file changes;
- reject symlinks inside declared output directories.

## 0.2.0 - 2026-11-18

- add durable `build/main` baselines and sparse `build/pr/<number>` overlays;
- add overlay resolution and scoped promotion;
- add stable/preview Pages handling with provenance;
- add normal-push generated-branch publication with source freshness checks and retry;
- add a shared HTML page framework while keeping consumer CSS and content local;
- add documentation Pages built with the same framework.

## 0.1.0 - 2026-11-18

Initial `tool.cad.ci` implementation:

- discover CI items from repository folder patterns;
- keep item behaviour in each folder's `ci.yml`;
- select affected items from changed files or exact Git revisions;
- order item dependencies;
- print the build plan without running it;
- run complete items or selected step ranges;
- save step state and declared output hashes under the item's build path;
- reuse output only while inputs, dependencies, commands and output files still match.
