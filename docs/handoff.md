# tool.cad.ci handoff

Repository: `brainboxemb/tool.cad.ci`.

This document is the easy-to-find handoff entrypoint for a new work session.
It contains one copyable handoff message below.

The handoff message is deliberately an entrypoint, not a second repository
plan. Current work must always be derived from live GitHub state and
`docs/plan.md`.

Shared SolidCraft/CAD documentation conventions live in
`brainboxemb/meta.cad.solidcraft`. Use
`templates/docs/plan.md` and `templates/docs/handoff.md` there as structural
references.

## Handoff message

Copy the complete text block below into a new chat.

~~~text
You are continuing work on brainboxemb/tool.cad.ci.

Repository role:

- provide the released CLI and GitHub Actions adapters above lib.py.cad.ci;
- keep generic CAD-CI algorithms and execution semantics in lib.py.cad.ci
  rather than reimplementing them here;
- qualify the released tool/library stack in tool.cad.ci.test before consumer
  repositories migrate to a new tool release.

Use this handoff only as the entrypoint. Do not treat copied handoff text as
fresher than GitHub or the repository plan.

Start by:

1. inspecting the current issues, pull requests and branches;
2. reading AGENTS.md;
3. reading docs/plan.md;
4. treating docs/plan.md as the source of truth for unfinished work;
5. following the current work order from the plan rather than from old handoff
   text;
6. creating an issue before implementation when the logical change has none;
7. keeping one logical change to one issue, branch and PR;
8. updating requirements/design documentation when behavior or architecture
   changes;
9. reconciling the plan after merge or release.

Durable working rules:

- do not add generic CI behavior or consumer-specific workarounds to this tool
  when the owning behavior belongs in lib.py.cad.ci;
- consumers pin immutable released tool revisions and start from the canonical
  templates under docs/manual/templates/;
- keep the documented one-runner workflow/action boundaries intact unless an
  explicit architecture change is accepted and tested.

Shared document structures live in brainboxemb/meta.cad.solidcraft:
templates/docs/plan.md and templates/docs/handoff.md.

Do not copy exact current SHAs, runtime/release pins, active issue/PR status,
temporary migration phases or a short-lived "next actions" list into this
handoff. Those facts belong in GitHub and docs/plan.md.
~~~

## Template guidance

The text block above is the actual handoff message.

Everything outside that block only explains how to use or maintain the
document. A consumer may translate the copyable message to the user's normal
chat language when that is intentional; repository-maintained explanatory text
outside the block remains English.

Keep repository-specific durable role and ownership guidance in the block when
it helps route work correctly. Do not turn the handoff into a status snapshot.
