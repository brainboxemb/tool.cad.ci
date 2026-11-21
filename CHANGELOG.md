# Changelog

## 0.16.1 - 2026-11-21

- consume released `lib.py.cad.ci 0.9.2` at exact commit
  `3f688243f4ee65b1fa42f82adde5344fe5101775`;
- restore durable publication compatibility with current SCons engine-schema-2
  evidence;
- change no CLI, workflow, named-scope or publication semantics.

## 0.16.0 - 2026-11-21

- consume released `lib.py.cad.ci 0.9.1` at exact commit
  `8403c426776dbad5beb17c35674562dc916e9a1f`;
- expose complete caller-named build-scope prepare/update/install/publication
  commands without adding tool-owned reconciliation semantics;
- expose isolated named Pages subtree publication and explicit stable-root
  named-subtree preservation;
- keep existing main and PR publication commands compatible.

## 0.15.0 - 2026-11-21

- add a released root composite action for consumers that require
  consumer-owned post-run steps on the same hosted runner;
- use the exact action revision as tool source and shallow-check out only its
  exact pinned library source;
- expose the exact tool/library stack through `PYTHONPATH` to subsequent
  caller steps without installing either BrainboxEmb package;
- perform the existing generic source/base checkout, external dependency setup,
  GHCR authentication and one `cad-ci run` without build-artifact transport;
- keep consumer post-run commands, build-store policy and Pages content outside
  the action.


## 0.14.2 - 2026-11-20

- consume `lib.py.cad.ci` 0.8.4 at exact commit
  `4e033fd17e911b3feb92b1a34433b884ca788ab6`;
- pass affected replacement items and the complete current processed item set
  separately to library-owned durable main updates;
- add no tool-owned manifest comparison, deletion or ownership semantics.

## 0.14.1 - 2026-11-20

- fetch only the exact caller PR head and required base commit instead of all
  branches, tags and history;
- authenticate GHCR directly through the runner Docker CLI;
- install external PR runtime dependencies without dependency recursion or
  eager bytecode compilation;
- add no persistent Actions cache and change no CAD-CI/SCons semantics.


## 0.14.0 - 2026-11-20

- add one complete reusable PR workflow for run, durable PR preparation,
  publication and cleanup on one runner;
- remove the PR artifact handoff and second publication runner from the generic
  PR architecture;
- execute the exact tool and pinned library source directly through PYTHONPATH
  instead of editable-installing/building the BrainboxEmb packages on every
  consumer PR;
- keep SCons execution, selection, build-store and publication semantics in
  lib.py.cad.ci.


## 0.13.3 - 2026-11-20

- consume `lib.py.cad.ci` 0.8.3 at exact commit `e8e951ed7e50c4fa754cc158729faf2927cccb31`;
- expose live streamed CAD-CI execution output and concise SCons action labels through the existing thin CLI;
- add no tool-owned SCons, logging, selection, cache or publication semantics.

## 0.13.2 - 2026-11-20

- consume `lib.py.cad.ci` 0.8.2 at exact commit `d645b65281064f69f175bb645c6c956f72f3b446`;
- expose ownership-safe nested durable build preparation/update through the existing thin CLI;
- add no tool-owned build-store, selection, SCons or cache semantics.

## 0.13.1 - 2026-11-20

- consume `lib.py.cad.ci` 0.8.1 at exact commit `ab701bf9ef46892040f4593a74b16805b7187bea`;
- expose safe parent-relative item-scoped source paths through the existing thin CLI;
- add no tool-owned path, selection or cache semantics.

## 0.13.0 - 2026-11-20

- consume `lib.py.cad.ci` 0.8.0 at exact commit `e2056c0d5ac361f0d021e58e55025e02c5688acf`;
- expose item-root-relative source paths, root item templates and path-derived nested item IDs through the existing thin CLI;
- add no tool-owned configuration, selection or cache semantics.

## 0.12.3 - 2026-11-20

- make `cad-ci build prepare-main` use the released library full-run selection;
- exclude configured `process: false` items from complete main candidates;
- keep `process` semantics owned by `lib.py.cad.ci`.

## 0.12.2 - 2026-11-20

- keep successful reusable CAD-CI runs successful when `upload_build: true` but no materialized `build/` output exists;
- expose/upload the build artifact only when materialized build output is present;
- keep build selection/materialization semantics owned by `lib.py.cad.ci`.

## 0.12.1 - 2026-11-20

- consume `lib.py.cad.ci` 0.7.1 at exact commit `c031f5dce3a4b0b207d8ce24716b5e11cdd12df2`;
- pick up the build-store evidence-schema compatibility fix found by external acceptance;
- make no CLI, workflow or CAD-CI behavior changes in the tool.

## 0.12.0 - 2026-11-20

- consume `lib.py.cad.ci` 0.7.0 at exact commit `8955c74055105b06d6af69e0d2f82b6b1fbf575a`;
- expose UTC run/action timing fields and updated public evidence schemas through the existing thin CLI without duplicating timing logic;
- cancel superseded high-level reusable CAD-CI runs for the same caller repository, workflow and PR/branch;
- keep lower-level reusable plan/run workflows independent for split consumers;
- keep CAD item selection, SCons execution and duration semantics owned by the library.

## 0.11.0 - 2026-11-20

- consume `lib.py.cad.ci` 0.6.0 at exact commit `dac8c5b5e1147a401730fda31f9bf9de2278c4ee`;
- expose item-level `process` participation through the existing thin plan/run CLI without duplicating library logic;
- prove `process: false` is excluded from full planning and rejected for explicit execution;
- require black-box acceptance in `tool.cad.ci.test` before Forge adoption.

## 0.10.0 - 2026-11-20

- authenticate Docker to GitHub Container Registry in the reusable run workflow with the workflow GitHub token;
- preserve `packages: read` through both reusable workflow layers;
- keep registry authentication generic and independent of consumer image names;
- leave CAD-CI planning/execution behavior in `lib.py.cad.ci` unchanged;
- require black-box acceptance in `tool.cad.ci.test` before consumer adoption.


## 0.9.0 - 2026-11-19

- consume `lib.py.cad.ci` 0.5.0 at exact commit `345794521fe162eb1908e1e8f38a6eabb02c8290`;
- expose repository-wide root `cad-ci.yml:variables` through the existing thin CLI/workflow stack without duplicating parsing or merge logic;
- document environment precedence between caller values, repository variables and CAD-CI-owned runtime values.


## 0.8.0 - 2026-11-19

- remove implicit GitHub Actions cache restore/save from reusable CAD-CI workflows;
- keep SCons job-local private state separate from durable build output;
- preserve one generic CAD-CI run and optional build-artifact handoff without persistent cache side effects.


## 0.7.1 - 2026-11-19

- key the reusable GitHub Actions CAD-CI cache by exact source commit instead of workflow run/attempt;
- reuse the same cache record when the same source commit is rerun;
- preserve prefix fallback so a new source commit can restore the newest compatible SCons state without requiring cache-delete permissions.

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
