# Change records

This directory contains design and migration decisions for
`tool.cad.ci`.

Change records use their own sequential four-digit number:

```text
0001-short-name.md
0002-short-name.md
...
```

A change record is not the same as an issue or pull request.

One change may:
- identify several implementation issues;
- be completed through several pull requests;
- affect `tool.cad.ci`, its external acceptance repository and multiple
  consumers;
- remain the stable design record after those issues and pull requests close.

Issues track executable work and current blockers. Pull requests implement
pieces of that work. Change records explain the decision, its boundaries,
migration and acceptance criteria.

Do not renumber an existing change record. Add a new record when a later design
decision materially changes the contract.

## Records

| Change | Status | Subject |
| --- | --- | --- |
| [0001](0001-cad-ci-consumer-interface.md) | proposed | Make the public CAD-CI consumer interface literal, consistent and usable from Forge and product CAD. |
