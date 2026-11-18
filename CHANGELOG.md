# Changelog

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
