# Changelog

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
