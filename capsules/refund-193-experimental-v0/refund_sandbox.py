#!/usr/bin/env python3
"""Bounded refund execution primitive for the federation sandbox.

This module deliberately starts *after* approval admission.  It does not verify
PIC or APS evidence, decide whether a merchant approval is legitimate, or
consume approvals.  It receives one already-admitted logical operation and
owns execution identity, dispatch, retry, reconciliation, and observed result
evidence for the local simulator.
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import re
import time
import uuid
from pathlib import Path
from typing import Any

INPUT_SCHEMA = "refund-execution/0.1"
RESULT_SCHEMA = "refund-execution-result/0.1"
_ALLOWED_STATUS = {"observed_success", "observed_failure", "unresolved"}
_CURRENCY = re.compile(r"^[A-Z]{3}$")


class RefundExecutionError(Exception):
    pass


class BindingMismatch(RefundExecutionError):
    pass


class SimulatedResponseLost(RefundExecutionError):
    pass


def stable_sha256(value: Any) -> str:
    raw = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def canonical_arguments(value: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise RefundExecutionError("arguments-object-required")
    if set(value) != {"payment_id", "amount_minor", "currency"}:
        raise RefundExecutionError("arguments-exact-fields-required")
    payment_id = value.get("payment_id")
    currency = value.get("currency")
    amount_minor = value.get("amount_minor")
    if not isinstance(payment_id, str) or not payment_id.strip():
        raise RefundExecutionError("payment-id-required")
    if not isinstance(currency, str) or not _CURRENCY.fullmatch(currency):
        raise RefundExecutionError("currency-must-be-uppercase-iso4217")
    if isinstance(amount_minor, bool) or not isinstance(amount_minor, int) or amount_minor <= 0 or amount_minor > (2**53 - 1):
        raise RefundExecutionError("amount-minor-must-be-positive-integer")
    return {
        "payment_id": payment_id,
        "currency": currency,
        "amount_minor": amount_minor,
    }


def validate_admitted_operation(value: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise RefundExecutionError("operation-object-required")
    if value.get("schema") != INPUT_SCHEMA:
        raise RefundExecutionError("unsupported-input-schema")
    operation_id = value.get("operation_id")
    tool = value.get("tool")
    if not isinstance(operation_id, str) or not operation_id.strip():
        raise RefundExecutionError("operation-id-required")
    if tool != "refund":
        raise RefundExecutionError("refund-tool-required")
    arguments = canonical_arguments(value.get("arguments"))
    refs = {}
    for field in ("approval_ref", "pic_evidence_ref", "aps_evidence_ref"):
        item = value.get(field)
        if not isinstance(item, str) or not item.strip():
            raise RefundExecutionError(f"{field}-required")
        refs[field] = item
    return {
        "schema": INPUT_SCHEMA,
        "operation_id": operation_id,
        "tool": tool,
        "arguments": arguments,
        **refs,
    }


def binding_material(operation: dict[str, Any]) -> dict[str, Any]:
    return {
        "operation_id": operation["operation_id"],
        "tool": operation["tool"],
        "arguments": operation["arguments"],
        "approval_ref": operation["approval_ref"],
        "pic_evidence_ref": operation["pic_evidence_ref"],
        "aps_evidence_ref": operation["aps_evidence_ref"],
    }


class LocalRefundSimulator:
    """Durable, local-only provider simulator with idempotent effects."""

    def __init__(self, state_dir: Path):
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.effects_path = self.state_dir / "effects.json"
        self.lock_path = self.state_dir / "effects.lock"

    def _load(self) -> dict[str, Any]:
        if not self.effects_path.exists():
            return {}
        return json.loads(self.effects_path.read_text())

    def _save(self, value: dict[str, Any]) -> None:
        tmp = self.effects_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n")
        os.replace(tmp, self.effects_path)

    def dispatch(
        self,
        *,
        idempotency_key: str,
        operation_id: str,
        arguments: dict[str, Any],
        lose_response_after_commit: bool = False,
    ) -> dict[str, Any]:
        with self.lock_path.open("a+") as lock:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
            effects = self._load()
            existing = effects.get(idempotency_key)
            if existing is None:
                existing = {
                    "effect_ref": f"sim-refund-{uuid.uuid4()}",
                    "operation_id": operation_id,
                    "arguments": arguments,
                    "arguments_digest": stable_sha256(arguments),
                    "recorded_at": time.time(),
                }
                effects[idempotency_key] = existing
                self._save(effects)
                if lose_response_after_commit:
                    raise SimulatedResponseLost("response-lost-after-effect")
            else:
                if (
                    existing.get("operation_id") != operation_id
                    or existing.get("arguments_digest") != stable_sha256(arguments)
                ):
                    raise BindingMismatch("simulator-idempotency-binding-mismatch")
            return dict(existing)

    def observe(self, idempotency_key: str) -> dict[str, Any] | None:
        with self.lock_path.open("a+") as lock:
            fcntl.flock(lock.fileno(), fcntl.LOCK_SH)
            value = self._load().get(idempotency_key)
            return dict(value) if value is not None else None

    def effect_count(self) -> int:
        with self.lock_path.open("a+") as lock:
            fcntl.flock(lock.fileno(), fcntl.LOCK_SH)
            return len(self._load())


class RefundExecutionEngine:
    def __init__(self, state_dir: Path, simulator: LocalRefundSimulator | None = None):
        self.state_dir = Path(state_dir)
        self.operations_dir = self.state_dir / "operations"
        self.operations_dir.mkdir(parents=True, exist_ok=True)
        self.lock_path = self.state_dir / "operations.lock"
        self.simulator = simulator or LocalRefundSimulator(self.state_dir / "simulator")

    def _path(self, operation_id: str) -> Path:
        return self.operations_dir / f"{hashlib.sha256(operation_id.encode()).hexdigest()}.json"

    def _load_record(self, operation_id: str) -> dict[str, Any] | None:
        path = self._path(operation_id)
        return json.loads(path.read_text()) if path.exists() else None

    def _save_record(self, record: dict[str, Any]) -> None:
        path = self._path(record["operation_id"])
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(record, sort_keys=True, indent=2) + "\n")
        os.replace(tmp, path)

    def _ensure_record(self, operation: dict[str, Any]) -> dict[str, Any]:
        operation_id = operation["operation_id"]
        current = self._load_record(operation_id)
        material = binding_material(operation)
        binding_digest = stable_sha256(material)
        arguments_digest = stable_sha256(operation["arguments"])
        if current is not None:
            if current.get("binding_digest") != binding_digest:
                raise BindingMismatch("operation-binding-mismatch")
            return current
        record = {
            "schema": "refund-operation-state/0.1",
            "operation_id": operation_id,
            "approval_ref": operation["approval_ref"],
            "binding_digest": binding_digest,
            "arguments_digest": arguments_digest,
            "arguments": operation["arguments"],
            "idempotency_key": stable_sha256(
                {"purpose": "refund-provider-idempotency", "operation_id": operation_id}
            ),
            "status": "admitted",
            "effect_ref": None,
            "attempts": [],
            "created_at": time.time(),
            "updated_at": time.time(),
        }
        self._save_record(record)
        return record

    def _result(self, record: dict[str, Any], attempt_id: str) -> dict[str, Any]:
        status = record["status"]
        if status not in _ALLOWED_STATUS:
            raise RefundExecutionError("operation-not-yet-observed")
        observation = {
            "operation_id": record["operation_id"],
            "attempt_id": attempt_id,
            "status": status,
            "effect_ref": record.get("effect_ref"),
            "arguments_digest": record["arguments_digest"],
        }
        return {
            "schema": RESULT_SCHEMA,
            **observation,
            "observation_ref": stable_sha256(observation),
        }

    def execute(
        self,
        admitted_operation: dict[str, Any],
        *,
        fail_before_dispatch: bool = False,
        lose_response_after_commit: bool = False,
    ) -> dict[str, Any]:
        operation = validate_admitted_operation(admitted_operation)
        attempt_id = str(uuid.uuid4())

        with self.lock_path.open("a+") as lock:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
            record = self._ensure_record(operation)

            if record["status"] == "observed_success":
                record["attempts"].append(
                    {"attempt_id": attempt_id, "kind": "duplicate", "status": "observed_success"}
                )
                record["updated_at"] = time.time()
                self._save_record(record)
                return self._result(record, attempt_id)

            if record["status"] == "observed_failure":
                record["attempts"].append(
                    {"attempt_id": attempt_id, "kind": "duplicate", "status": "observed_failure"}
                )
                record["updated_at"] = time.time()
                self._save_record(record)
                return self._result(record, attempt_id)

            if fail_before_dispatch:
                record["status"] = "observed_failure"
                record["attempts"].append(
                    {
                        "attempt_id": attempt_id,
                        "kind": "dispatch",
                        "status": "observed_failure",
                        "reason": "failed-before-dispatch",
                    }
                )
                record["updated_at"] = time.time()
                self._save_record(record)
                return self._result(record, attempt_id)

            try:
                effect = self.simulator.dispatch(
                    idempotency_key=record["idempotency_key"],
                    operation_id=record["operation_id"],
                    arguments=record["arguments"],
                    lose_response_after_commit=lose_response_after_commit,
                )
            except SimulatedResponseLost:
                record["status"] = "unresolved"
                record["attempts"].append(
                    {
                        "attempt_id": attempt_id,
                        "kind": "dispatch",
                        "status": "unresolved",
                        "reason": "response-lost-after-dispatch",
                    }
                )
                record["updated_at"] = time.time()
                self._save_record(record)
                return self._result(record, attempt_id)

            record["status"] = "observed_success"
            record["effect_ref"] = effect["effect_ref"]
            record["attempts"].append(
                {"attempt_id": attempt_id, "kind": "dispatch", "status": "observed_success"}
            )
            record["updated_at"] = time.time()
            self._save_record(record)
            return self._result(record, attempt_id)

    def reconcile(self, operation_id: str) -> dict[str, Any]:
        if not isinstance(operation_id, str) or not operation_id.strip():
            raise RefundExecutionError("operation-id-required")
        attempt_id = str(uuid.uuid4())
        with self.lock_path.open("a+") as lock:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
            record = self._load_record(operation_id)
            if record is None:
                raise RefundExecutionError("operation-not-found")
            if record["status"] == "observed_failure":
                record["attempts"].append(
                    {"attempt_id": attempt_id, "kind": "reconcile", "status": "observed_failure"}
                )
            else:
                effect = self.simulator.observe(record["idempotency_key"])
                if effect is None:
                    record["status"] = "unresolved"
                    record["attempts"].append(
                        {"attempt_id": attempt_id, "kind": "reconcile", "status": "unresolved"}
                    )
                else:
                    if (effect.get("operation_id") != record["operation_id"]
                            or effect.get("arguments_digest") != record["arguments_digest"]):
                        raise BindingMismatch("observed-effect-binding-mismatch")
                    record["status"] = "observed_success"
                    record["effect_ref"] = effect["effect_ref"]
                    record["attempts"].append(
                        {"attempt_id": attempt_id, "kind": "reconcile", "status": "observed_success"}
                    )
            record["updated_at"] = time.time()
            self._save_record(record)
            return self._result(record, attempt_id)
