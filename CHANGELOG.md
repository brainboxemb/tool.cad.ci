# Changelog

## 0.7.0 - 2026-11-19

- consume lib.py.cad.ci 0.4.0 at exact commit 73985ca9638bf7a5e3209bfd1d3896d043193bb2;
- expose public step evidence with `output_state` instead of `materialization`;
- expose restore failures as `output_restore_error` instead of `materialization_error`;
- print literal `output=...` target results and reject the old operator-facing terminology in CLI tests.


## 0.6.1 - 2026-11-19

- fix reusable build artifact name propagation to downstream caller jobs;
- align the artifact-name step id with the job output expression;
- add a regression test for the reusable workflow output contract.


## 0.6.0 - 2026-11-19

- add one high-level `reusable-ci.yml` entry point for normal consumers;
- keep `reusable-plan.yml` and `reusable-run.yml` as lower-level building blocks for consumers with domain setup between planning and execution;
- pass optional materialized `build/` output through a generic GitHub artifact for downstream publication or transformation jobs;
- keep hidden `.cad-ci` evidence in that artifact while excluding private `.cache/cad-ci` state;
- keep workflow, tool and library identity pinned to the exact released tool commit.


## 0.5.0 - 2026-11-19

- add reusable GitHub Actions workflows for generic CAD-CI planning and execution;
- tie the reusable workflow definition and installed tool to one exact commit through `job.workflow_repository` and `job.workflow_sha`;
- restore/save the SCons cache centrally in the reusable run workflow;
- expose compact plan JSON for consumers that need domain setup between planning and execution;
- support validated non-secret consumer environment values without duplicating generic workflow setup.


## 0.4.0 - 2026-11-19

- consume lib.py.cad.ci 0.3.0 at exact commit 155ec24915e7b2d1b9f5306db9df84a50b53dba8;
- run one SCons-backed repository graph per cad-ci run instead of executing items one by one;
- keep plan explanatory while SCons owns incremental target decisions;
- forward mutually exclusive step, until and from partial-run controls to the library;
- validate durable build scopes against .cad-ci SCons evidence;
- keep sparse PR overlays limited to selected top-level items;
- update CLI tests and documentation to the permanent tool.cad.ci.test acceptance flow.


## 0.3.2 - 2026-11-19

- add `cad-ci build fetch` for authenticated, read-only generated-branch materialization;
- delegate generated-branch Git handling to `lib.py.cad.ci` 0.1.3.

## 0.3.1 - 2026-11-19

- let prepare-pr and update-main derive sparse item selection from --base/--head or --changed;
- use the same lib.py.cad.ci affected/dependency plan as plan/run.

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
