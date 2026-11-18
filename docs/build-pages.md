# Build output and Pages

`tool.cad.ci` keeps technical output and public HTML separate.

## Build branch

The durable `build` branch has two scopes:

```text
main/
  build.json
  <item source path>/...
pr/
  <number>/
    build.json
    <affected item source path>/...
```

`main/` is a complete accepted baseline. A PR scope is a sparse overlay. It contains only items rebuilt by that PR.

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

Updating the stable site preserves every preview. Updating or cleaning one preview changes only that preview directory.

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
