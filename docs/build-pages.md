# Build output and Pages

`tool.cad.ci` keeps technical output and public HTML separate.

## Build branch

The durable `build` branch supports stable, named complete and PR scopes:

```text
main/
  build.json
  <item source path>/...
<name>/
  build.json
  <item source path>/...
pr/
  <number>/
    build.json
    <affected item source path>/...
```

`main/` and caller-named scopes are complete baselines. A PR scope is a
sparse overlay containing only items rebuilt by that PR. Named scopes use one
safe top-level path segment and are useful for long-lived integration lanes.

A normal main run does not need to rebuild the full catalog. `build update-main` copies the existing complete baseline, validates the selected fresh item results, replaces only those item directories, and writes a new complete manifest. New selected items may be added when the consumer catalog grows; unrelated baseline items are preserved.

A preview resolves the complete view by starting with `main/` and replacing the item paths present in the PR overlay. Promotion does the same replacement into a new complete `main/` candidate. Unaffected item directories are preserved.

The build manifest records the source commit and the input/result fingerprints for every stored item. The item directory also keeps the runner's `item.json` and per-step state.

## Pages branch

The `gh-pages` branch contains presentation output only:

```text
/
  index.html
  ...
  provenance.json
previews/
  pr-<number>/
    index.html
    ...
    provenance.json
```

A consumer may also publish complete sites below safe named top-level
subtrees, for example `dev/`.

Updating one named subtree preserves stable content, every PR preview and every
sibling named subtree. Updating the stable site preserves every PR preview and
the explicit named-subtree keep set supplied with
`--preserve-subtree <name>`. Updating or cleaning one PR preview changes only
that preview directory.

`provenance.json` is written by the site build and should identify the source commit and build evidence used for that site.

## Shared site framework

The library provides the base HTML structure and navigation. A consumer supplies:

- page titles;
- page body HTML;
- its own stylesheet;
- the correct Pages base path;
- provenance values.

The framework deliberately does not impose Forge/CAD branding or CSS.

## Git publication

Generated branches are never force-pushed.

For every write the publisher:

1. checks that the source branch still points to the expected source commit;
2. clones the current generated branch head;
3. applies one scoped filesystem change;
4. commits it;
5. checks source freshness again;
6. pushes normally;
7. retries from the new branch head when another writer won the race.

This means correctness does not depend on GitHub Actions concurrency behaving like a queue.

## Named scope commands

Complete named build state uses the same released library semantics as
`main`:

```text
cad-ci build prepare-named --name <name> ...
cad-ci build update-named --name <name> --named <existing-scope> ...
cad-ci publish build --scope named --scope-name <name> ...
```

Named Pages publication and stable-root preservation are exposed as:

```text
cad-ci publish pages --name <name> --site <site> ...
cad-ci publish pages --site <stable-site> \
  --preserve-subtree <name-a> \
  --preserve-subtree <name-b> ...
```

The tool forwards these values to the released library. It does not implement
scope reconciliation or path-safety rules itself.
