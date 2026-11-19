"""Turn changed files and item dependencies into an ordered build plan."""

from __future__ import annotations

from dataclasses import dataclass

from .model import Item
from .paths import matches


@dataclass(frozen=True)
class PlanEntry:
    """One item in the execution order and the reason it was included."""

    item: Item
    reason: str


def affected_items(
    items: dict[str, Item],
    changed_files: tuple[str, ...] | None,
) -> set[str]:
    """Return items that must be reconsidered for the supplied file changes.

    `None` means an explicit full run. An empty tuple means no files changed.
    """

    if changed_files is None:
        return set(items)

    # The root file controls item discovery. A change can add/remove items or
    # change folder patterns, so selecting every item is the safe behaviour.
    if "cad-ci.yml" in changed_files:
        return set(items)

    affected: set[str] = {
        item.id for item in items.values() if item.affected == "always"
    }
    for item in items.values():
        item_config = (item.path / "ci.yml").as_posix()
        if item_config in changed_files:
            affected.add(item.id)
            continue
        if any(
            matches(changed, pattern)
            for changed in changed_files
            for pattern in item.watch
        ):
            affected.add(item.id)

    # A changed dependency can change every item that consumes its output.
    # Repeat until stable because dependency chains can be several items deep.
    changed = True
    while changed:
        changed = False
        for item in items.values():
            # direct items are selected only by their own watched/config paths,
            # an explicit --item request, or a full run. This is useful for
            # summary/aggregate items: a change in one dependency should not
            # automatically pull every sibling dependency into an incremental run.
            if item.affected == "direct":
                continue
            if item.id not in affected and any(dep in affected for dep in item.needs):
                affected.add(item.id)
                changed = True
    return affected


def build_plan(
    items: dict[str, Item],
    selected: set[str],
) -> list[PlanEntry]:
    """Return dependencies before the selected items that need them."""

    needed = set(selected)

    def add_dependencies(item_id: str) -> None:
        # Dependencies are included even when their own source did not change.
        # Their saved result may be needed to validate or run the selected item.
        for dependency in items[item_id].needs:
            if dependency not in needed:
                needed.add(dependency)
                add_dependencies(dependency)

    for item_id in tuple(selected):
        add_dependencies(item_id)

    ordered: list[PlanEntry] = []
    done: set[str] = set()

    def add(item_id: str) -> None:
        if item_id in done or item_id not in needed:
            return
        item = items[item_id]
        for dependency in item.needs:
            add(dependency)
        reason = "affected" if item_id in selected else "dependency"
        ordered.append(PlanEntry(item, reason))
        done.add(item_id)

    # Iterating repository order keeps the plan stable when two independent
    # items have no ordering requirement between them.
    for item_id in items:
        add(item_id)
    return ordered
