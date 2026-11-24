# 0001 — Simple CAD-CI consumer contract

Status: **proposed**

Initial tracker: `tool.cad.ci #174`.

This change records the consumer behavior we want from CAD-CI. It deliberately
does not redesign the CAD-CI engine or create a new set of abstractions.

## Problem

The current consumer setup has become difficult to understand because normal
behavior is spread across several workflow/template names and described with
terms such as:

- durable;
- lane;
- scope;
- qualification;
- probe;
- promotion.

A repository owner should not need to read the reusable workflow
implementation to answer:

- what happens on a pull request;
- what happens after a push to a permanent branch;
- how to run everything manually;
- how to run one selected item;
- what gets published.

The immediate goal is a working and predictable CI setup, not a broad internal
cleanup.

## Owners

The existing ownership remains:

- `lib.py.cad.ci` — generic CAD-CI engine, selection, SCons/build execution
  and build-store behavior;
- `tool.cad.ci` — released GitHub workflow integration;
- consumer repository — repository config, builders and model/project content.

Do not move generic CAD-CI behavior into Forge or a product CAD repository.

## Consumer audit

The two real consumers are:

- `brainboxemb/lib.py.solidcraft.forge`;
- `brainboxemb/2026-011-02.cad.solidcraft`.

They use the same generic CI model.

### Forge

Current intended behavior:

- pull request: build/test/verify only;
- push to `main`, `dev-cad` or `dev-ci`: build and publish that branch's
  accepted generated output;
- manual selected execution: read-only;
- deliberate full execution must be possible.

Forge does not need PR build publication.

### Product CAD

The base CI behavior should be the same:

- pull request: build/test/verify only;
- push to `main`, `dev-cad` or `dev-ci`: build and publish that branch's
  accepted generated output;
- manual selected execution: read-only;
- deliberate full execution must be possible.

Product CAD also does **not** publish normal PR build/Page state as part of the
base CI contract.

Reviewing an exact PR render is a separate review/output problem. It must not
make the normal CI contract different from Forge.

## Required behavior

There are only three normal CI operations.

### 1. Pull request

```text
pull request
  -> select affected work
  -> build
  -> test
  -> verify
  -> publish nothing
```

Requirements:

- exact PR head is tested;
- normal changed-item/dependency selection comes from released CAD-CI;
- a branch-policy rule may require a full run for a permanent development
  branch -> stable branch PR;
- no generated `build/pr/...` output;
- no Pages publication;
- no Actions artifact transport as part of the base CI contract.

Forge and product CAD use the same behavior.

### 2. Push to a permanent branch

```text
push main/dev-cad/dev-ci
  -> select affected work
  -> build
  -> test
  -> verify
  -> publish complete build/<branch>
  -> publish configured Pages output
```

Requirements:

- one shared implementation for `main` and configured development branches;
- generated output records the exact source commit;
- unchanged accepted model output remains available in the complete branch
  build;
- Pages is presentation output, not the release/build evidence source.

### 3. Manual run

The operator chooses one explicit read-only mode:

```text
full
item
changed_paths
```

Behavior:

```text
manual
  -> build
  -> test
  -> verify
  -> publish nothing
```

Requirements:

- `full` executes every configured processed item;
- `item` executes one exact configured item;
- `changed_paths` uses the normal generic affected-item selection;
- leaving fields empty must not silently change the operation into branch
  publication;
- manual selected/full execution does not partially overwrite a permanent
  branch build.

## One template repository

Use the existing `brainboxemb/tool.cad.ci.test` repository as the living
reference consumer.

Do not create another template repository.

`tool.cad.ci.test` already has the correct ownership rule: it must look like a
normal consumer and must not contain a second CAD-CI implementation. Its live
consumer files therefore become the copy/reference source once the new contract
is accepted.

It must demonstrate the complete normal setup:

```text
.github/workflows/cad-ci.yml
cad-ci.yml
ci/
AGENTS.md
docs/plan.md
```

New repositories copy/adapt that known-working structure from
`tool.cad.ci.test`.

Forge and product CAD should be aligned with the same reference structure
rather than independently interpreting several templates.

Do not create multiple template variants for Forge vs product CAD.

## Public language

Current consumer-facing documentation and workflow UI should use literal
engineering terms:

- pull request;
- branch build;
- manual full run;
- manual selected run;
- build;
- test;
- verify;
- publish;
- source commit;
- build output;
- Pages.

Do not require users to understand these terms for normal operation:

- durable;
- lane;
- scope;
- qualification;
- probe;
- promotion.

Historical release notes and immutable old tags are not rewritten. Old names
may be mentioned only when documenting migration from an old interface.

## What not to change now

This change does not require:

- a rewrite of `lib.py.cad.ci`;
- a second CAD-CI engine;
- consumer-local selection or publication logic;
- PR build publication;
- PR Pages previews;
- Actions artifacts for normal CAD review;
- redesign of release handling;
- redesign of merge policy;
- solving duplicate-looking post-merge runs;
- broad internal function renaming before the consumer setup works.

If an existing internal name can remain temporarily without confusing a normal
consumer, leave it alone until there is a concrete reason to change it.

## Acceptance repository

Use `tool.cad.ci.test` as the black-box proof of the released consumer
contract.

It must prove, through released public surfaces:

1. normal PR build/test/verify with no publication;
2. permanent development-branch build/publication;
3. stable `main` build/publication;
4. manual full read-only run;
5. manual exact-item read-only run;
6. manual changed-path read-only run.

The acceptance repository must consume CAD-CI like a normal repository. It must
not contain a second planner or publisher.

## Real consumer acceptance

After the shared setup is released and externally accepted:

### Forge

- copy/align with the one reference consumer structure;
- keep repository-specific builders/config only;
- prove PR, branch and manual behavior.

### Product CAD

- copy/align with the same reference consumer structure;
- remove obsolete local generic orchestration;
- prove the same PR, branch and manual behavior;
- keep model/repository-specific build and site configuration in the CAD repo.

Neither consumer is used as the experiment that defines the generic behavior.

## Implementation order

1. Accept this change record.
2. Make `tool.cad.ci.test` the living reference consumer for that contract.
3. Make its normal consumer workflow/config pass all six acceptance cases.
4. Release the exact accepted `tool.cad.ci` version.
5. Align Forge with the template.
6. Align product CAD with the same template.
7. Only then remove superseded template/workflow documentation that is no
   longer used.

Do not start unrelated cleanup while this chain is in progress.

## Completion

Change 0001 is complete when:

- `tool.cad.ci.test` is the one obvious working consumer reference;
- Forge and product CAD follow the same base CI behavior;
- PRs never publish normal build/Page state;
- permanent branches publish complete branch build/Page output;
- manual full/item/changed-path runs are explicit and read-only;
- `tool.cad.ci.test` proves the released behavior black-box;
- normal consumer documentation does not require the rejected abstract terms;
- no consumer implements a local CAD-CI planner/build store/publisher.
