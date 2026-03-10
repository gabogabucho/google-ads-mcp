"""Safety guards and audit logging for write operations.

All mutating tools go through these checks before executing.
Plans are stored in-memory with a short UUID so Claude can
reference them without resending all parameters.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from .config import SafetyConfig


# ── Plan store (in-memory, per server process) ────────────────────────────────

@dataclass
class Plan:
    id: str
    operation: str
    description: str
    params: Dict[str, Any]
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


_plans: Dict[str, Plan] = {}


def create_plan(operation: str, description: str, params: Dict[str, Any]) -> Plan:
    plan_id = str(uuid.uuid4())[:8]
    plan = Plan(id=plan_id, operation=operation, description=description, params=params)
    _plans[plan_id] = plan
    return plan


def get_plan(plan_id: str) -> Optional[Plan]:
    return _plans.get(plan_id)


def consume_plan(plan_id: str) -> Optional[Plan]:
    """Retrieve and remove a plan (single-use)."""
    return _plans.pop(plan_id, None)


# ── Safety checks ─────────────────────────────────────────────────────────────

class SafetyError(ValueError):
    """Raised when a proposed change violates safety limits."""


def check_budget(proposed_usd: float, config: SafetyConfig) -> None:
    if proposed_usd > config.max_daily_budget_usd:
        raise SafetyError(
            f"Proposed budget ${proposed_usd:.2f} exceeds the configured limit "
            f"${config.max_daily_budget_usd:.2f}. "
            f"Adjust `safety.max_daily_budget_usd` in config.yaml to increase."
        )


def check_bid_increase(current_usd: float, proposed_usd: float, config: SafetyConfig) -> None:
    if current_usd <= 0:
        return
    pct = (proposed_usd - current_usd) / current_usd * 100
    if pct > config.max_bid_increase_pct:
        raise SafetyError(
            f"Bid increase of {pct:.0f}% exceeds the configured limit "
            f"{config.max_bid_increase_pct}%. "
            f"Adjust `safety.max_bid_increase_pct` in config.yaml."
        )


def check_operation_allowed(operation: str, config: SafetyConfig) -> None:
    if operation in config.blocked_operations:
        raise SafetyError(
            f"Operation '{operation}' is in the blocked list. "
            f"Remove it from `safety.blocked_operations` in config.yaml to allow."
        )


# ── Audit log ─────────────────────────────────────────────────────────────────

def audit_log(log_path: str, operation: str, entity: str, change: str, dry_run: bool) -> None:
    path = Path(log_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = "DRY-RUN" if dry_run else "APPLIED"
    entry = f"{datetime.now().isoformat()} | {mode} | {operation} | {entity} | {change}\n"
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(entry)
