from __future__ import annotations

from dataclasses import dataclass

from .model import Item
from .paths import matches


@dataclass(frozen=True)
class PlanEntry:
    item: Item
    reason: str


def affected_items(
    items: dict[str, Item],
    changed_files: tuple[str, ...] | None,
) -> set[str]:
    if changed_files is None:
        return set(items)
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

    # A changed dependency can change the result of every item that uses it.
    changed = True
    while changed:
        changed = False
        for item in items.values():
            if item.id not in affected and any(dep in affected for dep in item.needs):
                affected.add(item.id)
                changed = True
    return affected


def build_plan(
    items: dict[str, Item],
    selected: set[str],
) -> list[PlanEntry]:
    needed = set(selected)

    def add_dependencies(item_id: str) -> None:
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

    for item_id in items:
        add(item_id)
    return ordered
