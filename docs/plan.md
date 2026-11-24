# Repository plan

This file contains only unfinished work and current priority for
`tool.cad.ci`.

Completed release history belongs in GitHub releases, issues and change records,
not in this plan.

## Accepted baseline

- `tool.cad.ci v0.36.1` @
  `8a9acb8ea69581728a3850c658b4c1ae2db6ff5a`;
- released-stack acceptance is owned by `tool.cad.ci.test`;
- real consumers remain pinned to accepted releases until a newer exact stack
  passes external acceptance.

## Now

### #174 / Change 0001 — simple CAD-CI consumer contract

Change record:
`docs/changes/0001-cad-ci-consumer-interface.md`.

The base behavior is the same for Forge and product CAD:

```text
pull request
  -> build / test / verify
  -> publish nothing

push main/dev-cad/dev-ci
  -> build / test / verify
  -> publish complete branch build + configured Pages

manual
  -> full | item | changed_paths
  -> build / test / verify
  -> publish nothing
```

One living template repository should be the normal consumer reference.
Do not create separate Forge/CAD workflow variants.

Required order:

1. accept Change 0001;
2. make one working template consumer the reference;
3. make `tool.cad.ci.test` consume the same structure and prove PR, branch and
   manual routes;
4. release the exact accepted tool version;
5. align Forge;
6. align product CAD;
7. remove superseded template documentation only after both consumers work.

Do not broaden this work into release redesign, merge-policy redesign,
PR-output publication or internal cleanup that is not required for the working
consumer path.

## Next

### #180 — replace public `durable` language

Use literal branch-build language in the current consumer-facing surface.

Do this only where it improves the interface described by Change 0001.
Do not block the working consumer path on broad internal renaming.

### #172 — make Actions runs self-describing

Use the same literal operation names from Change 0001 in GitHub Actions
`run-name`/job presentation:

- pull request;
- branch build;
- manual full run;
- manual selected run.

Do not reintroduce old abstract mode names in the UI.

## Later

| Issue | Status |
| --- | --- |
| #175 duplicate-looking main/development runs | Investigate after the simple consumer path is stable. |
| #173 duplicate branch rebuild after permanent merge | Keep separate from Change 0001 unless a concrete correctness problem requires it. |
| #171 refresh permanent PR validation after branch updates | Separate lifecycle problem. |
| #170 permanent-branch conflict recovery | Separate merge-policy problem. |
| #164 reduce tool to shared workflows/governance adapters | Architectural cleanup after the consumer path is stable. |
| #117 historical changelog alignment | Documentation cleanup only. |

## Boundary

`tool.cad.ci` transports released CAD-CI behavior into GitHub Actions.

Generic selection, SCons execution and build-store algorithms belong in
`lib.py.cad.ci`.

Consumers own repository config, builders and project/model content. They must
not grow a second generic planner, build store or publisher.
