"""Execute one consumer-owned CI item and record reusable step state.

The runner validates complete dependency items before an item starts. Partial
step reruns never rebuild older steps implicitly: their saved state and output
must still match first.
"""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import time

from .model import Item, Step
from .state import (
    OutputHashError,
    item_input_fingerprint,
    read_json,
    sha256_output,
    step_input_fingerprint,
    step_result_fingerprint,
    write_json,
)


class RunError(RuntimeError):
    """Raised when an item cannot be executed with valid prerequisites."""


def item_output_dir(repo: Path, item: Item) -> Path:
    """Return the local build directory owned by one item."""

    return repo / "build" / item.path


def item_state_path(repo: Path, item: Item) -> Path:
    """Return the complete-item state file."""

    return item_output_dir(repo, item) / "item.json"


def step_state_path(repo: Path, item: Item, step: Step) -> Path:
    """Return the state file for one named step."""

    return item_output_dir(repo, item) / "steps" / f"{step.id}.json"


def _output_hashes(
    repo: Path,
    item: Item,
    step: Step,
) -> dict[str, str] | None:
    """Hash every declared step output, including complete directories.

    None means at least one declared output is missing. Unsafe symlinks are a
    configuration/result error and fail visibly instead of being treated as a
    reusable output.
    """

    base = item_output_dir(repo, item)
    result: dict[str, str] = {}
    for output in step.outputs:
        path = base / output
        try:
            value = sha256_output(path)
        except OutputHashError as exc:
            raise RunError(f"{item.id}:{step.id}: {exc}") from exc
        if value is None:
            return None
        result[output] = value
    return result


def _valid_step_result(
    repo: Path,
    item: Item,
    step: Step,
    input_fingerprint: str,
) -> str | None:
    """Return a saved result fingerprint only when state and output still match."""

    state = read_json(step_state_path(repo, item, step))
    if not state or state.get("status") != "pass":
        return None
    if state.get("input_fingerprint") != input_fingerprint:
        return None

    # Re-hash current output instead of trusting the saved hashes. A changed
    # file anywhere inside a declared directory therefore invalidates reuse.
    outputs = _output_hashes(repo, item, step)
    if outputs is None or outputs != state.get("outputs", {}):
        return None

    result = step_result_fingerprint(input_fingerprint, outputs)
    if state.get("result_fingerprint") != result:
        return None
    return result


def _current_item_result(
    repo: Path,
    item: Item,
    items: dict[str, Item],
    stack: tuple[str, ...] = (),
) -> str:
    """Validate one complete item recursively for dependency use."""

    if item.id in stack:
        raise RunError(f"dependency cycle while checking {item.id}")

    dependency_results: dict[str, str] = {}
    for dependency_id in item.needs:
        dependency = items[dependency_id]
        try:
            dependency_results[dependency_id] = _current_item_result(
                repo,
                dependency,
                items,
                stack + (item.id,),
            )
        except RunError as exc:
            raise RunError(
                f"{item.id} requires a current result for "
                f"{dependency_id}: {exc}"
            ) from exc

    item_fingerprint = item_input_fingerprint(
        repo,
        item,
        dependency_results,
    )
    previous_result: str | None = None
    for step in item.steps:
        input_fingerprint = step_input_fingerprint(
            item_fingerprint,
            step,
            previous_result,
        )
        result = _valid_step_result(
            repo,
            item,
            step,
            input_fingerprint,
        )
        if result is None:
            raise RunError(f"stale or missing step {item.id}:{step.id}")
        previous_result = result

    item_state = read_json(item_state_path(repo, item))
    if not item_state or item_state.get("status") != "pass":
        raise RunError(f"missing complete item result for {item.id}")
    if item_state.get("input_fingerprint") != item_fingerprint:
        raise RunError(f"stale item result for {item.id}")
    if item_state.get("result_fingerprint") != previous_result:
        raise RunError(f"stale item result for {item.id}")

    assert previous_result is not None
    return previous_result


def _dependency_results(
    repo: Path,
    item: Item,
    items: dict[str, Item],
) -> dict[str, str]:
    """Return validated complete results for every direct dependency."""

    result: dict[str, str] = {}
    for dependency_id in item.needs:
        dependency = items[dependency_id]
        try:
            result[dependency_id] = _current_item_result(
                repo,
                dependency,
                items,
            )
        except RunError as exc:
            raise RunError(
                f"{item.id} requires a current result for "
                f"{dependency_id}: {exc}"
            ) from exc
    return result


def _run_command(
    repo: Path,
    item: Item,
    step: Step,
) -> tuple[int, float]:
    """Run one configured command from its item folder with CAD_CI_* paths."""

    output_dir = item_output_dir(repo, item)
    output_dir.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    env.update(
        {
            "CAD_CI_REPO": str(repo),
            "CAD_CI_ITEM": item.id,
            "CAD_CI_ITEM_PATH": str(repo / item.path),
            "CAD_CI_OUTPUT": str(output_dir),
        }
    )

    started = time.monotonic()
    if isinstance(step.run, tuple):
        completed = subprocess.run(
            step.run,
            cwd=repo / item.path,
            env=env,
            check=False,
        )
    else:
        completed = subprocess.run(
            step.run,
            cwd=repo / item.path,
            env=env,
            shell=True,
            check=False,
        )
    return completed.returncode, time.monotonic() - started


def _step_range(
    item: Item,
    step: str | None,
    start: str | None,
    until: str | None,
) -> tuple[int, int, bool]:
    """Resolve exact/from/until selection to inclusive step indexes."""

    ids = [value.id for value in item.steps]
    for requested in (step, start, until):
        if requested is not None and requested not in ids:
            raise RunError(f"unknown step for {item.id}: {requested}")

    if step is not None:
        index = ids.index(step)
        return index, index, True

    first = ids.index(start) if start is not None else 0
    last = ids.index(until) if until is not None else len(ids) - 1
    if first > last:
        raise RunError(
            f"invalid step range for {item.id}: "
            f"{ids[first]} comes after {ids[last]}"
        )
    return first, last, start is not None


def run_item(
    repo: Path,
    item: Item,
    items: dict[str, Item],
    *,
    step: str | None = None,
    start: str | None = None,
    until: str | None = None,
) -> list[tuple[str, str]]:
    """Run or reuse the selected step range for one item.

    Exact/from reruns deliberately force the requested range. Earlier steps are
    only validated. A run that reaches the final step writes complete item
    state; an earlier partial run does not claim the item is complete.
    """

    dependency_results = _dependency_results(repo, item, items)
    item_fingerprint = item_input_fingerprint(
        repo,
        item,
        dependency_results,
    )
    first, last, force_range = _step_range(
        item,
        step,
        start,
        until,
    )

    previous_result: str | None = None
    events: list[tuple[str, str]] = []
    for index, current in enumerate(item.steps):
        input_fingerprint = step_input_fingerprint(
            item_fingerprint,
            current,
            previous_result,
        )
        valid_result = _valid_step_result(
            repo,
            item,
            current,
            input_fingerprint,
        )

        if index < first:
            # Do not rebuild older steps for a partial rerun. If their state is
            # stale, the caller must deliberately rerun from that point.
            if valid_result is None:
                raise RunError(
                    f"{item.id}:{item.steps[first].id} requires a current "
                    f"result for earlier step {current.id}"
                )
            previous_result = valid_result
            continue
        if index > last:
            break

        force = step is not None or force_range
        if item.reuse and not force and valid_result is not None:
            events.append((current.id, "reused"))
            previous_result = valid_result
            continue

        code, duration = _run_command(repo, item, current)
        outputs = _output_hashes(repo, item, current)
        status = "pass" if code == 0 and outputs is not None else "fail"
        result_fingerprint = (
            step_result_fingerprint(input_fingerprint, outputs)
            if outputs is not None
            else None
        )
        write_json(
            step_state_path(repo, item, current),
            {
                "step": current.id,
                "status": status,
                "input_fingerprint": input_fingerprint,
                "result_fingerprint": result_fingerprint,
                "duration_seconds": round(duration, 3),
                "exit_code": code,
                "outputs": outputs or {},
            },
        )

        if status != "pass":
            missing = (
                ""
                if outputs is not None
                else " or a declared output is missing"
            )
            raise RunError(
                f"step failed: {item.id}:{current.id} "
                f"(exit {code}{missing})"
            )

        events.append((current.id, "ran"))
        previous_result = result_fingerprint

    # Only a run that reaches the final step can leave a complete item result.
    if last == len(item.steps) - 1:
        write_json(
            item_state_path(repo, item),
            {
                "item": item.id,
                "status": "pass",
                "input_fingerprint": item_fingerprint,
                "result_fingerprint": previous_result,
            },
        )
    return events
