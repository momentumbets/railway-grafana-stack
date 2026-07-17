#!/usr/bin/env python3
"""Fail fast on GitOps alert inputs that Grafana would reject at startup."""

from __future__ import annotations

import json
import sys
from pathlib import Path

MAX_ALERT_RULE_UID_LENGTH = 40


def validate_alerting_directory(alerting_dir: Path) -> list[str]:
    errors: list[str] = []
    paths = sorted(alerting_dir.rglob("*.json"))
    if not paths:
        return [f"no JSON alert provisioning files found under {alerting_dir}"]

    for path in paths:
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"{path}: invalid JSON ({exc})")
            continue

        groups = document.get("groups") if isinstance(document, dict) else None
        if not isinstance(groups, list):
            errors.append(f"{path}: expected a top-level groups array")
            continue

        for group_index, group in enumerate(groups):
            if not isinstance(group, dict):
                errors.append(f"{path}: groups[{group_index}] must be an object")
                continue
            rules = group.get("rules")
            if not isinstance(rules, list):
                errors.append(f"{path}: group {group.get('name', group_index)!r} has no rules array")
                continue
            for rule_index, rule in enumerate(rules):
                if not isinstance(rule, dict):
                    errors.append(f"{path}: group {group.get('name', group_index)!r} rule {rule_index} must be an object")
                    continue
                uid = rule.get("uid")
                if not isinstance(uid, str) or not uid:
                    errors.append(f"{path}: group {group.get('name', group_index)!r} rule {rule_index} has no UID")
                elif len(uid) > MAX_ALERT_RULE_UID_LENGTH:
                    errors.append(
                        f"{path}: group {group.get('name', group_index)!r} rule UID {uid!r} is {len(uid)} characters; "
                        f"Grafana allows at most {MAX_ALERT_RULE_UID_LENGTH}"
                    )
    return errors


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(f"usage: {argv[0]} ALERTING_DIR", file=sys.stderr)
        return 2

    errors = validate_alerting_directory(Path(argv[1]))
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
