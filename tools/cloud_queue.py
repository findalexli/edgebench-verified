#!/usr/bin/env python3
# Copyright (c) 2026 EdgeBench Verified contributors
# SPDX-License-Identifier: Apache-2.0
"""Durable, conservative job accounting for the bounded cloud audit.

This module does not contact a provider or certify tasks. A launch intent is
committed before any remote mutation. Unknown outcomes cannot be retried here.
"""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
from decimal import Decimal, ROUND_CEILING
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import sqlite3
import stat
import uuid
from sol_audit_diagnostic_contract import CONTROLLER as SOL_AUDIT_V2_CONTROLLER, OPERATION as SOL_AUDIT_V2_OPERATION, validate_contract as validate_sol_audit_v2_contract
from sol_audit_contract import CONTROLLER as SOL_AUDIT_CONTROLLER, OPERATION as SOL_AUDIT_OPERATION, validate_contract as validate_sol_audit_contract

from vrptw_native_contract import CONTROLLER as VRPTW_CONTROLLER, OPERATION as VRPTW_OPERATION, validate_contract as validate_vrptw_contract

from vrptw_diagnostic_contract import CONTROLLER as VRPTW_DIAGNOSTIC_CONTROLLER, OPERATION as VRPTW_DIAGNOSTIC_OPERATION, validate_contract as validate_vrptw_diagnostic_contract
from sol_protocol_pilot_contract import CONTROLLER as SOL_PROTOCOL_V7_CONTROLLER, OPERATION as SOL_PROTOCOL_V7_OPERATION, validate_contract as validate_sol_protocol_v7_contract

from vrptw_environment_contract import CONTROLLER as VRPTW_ENVIRONMENT_CONTROLLER, OPERATION as VRPTW_ENVIRONMENT_OPERATION, validate_contract as validate_vrptw_environment_contract

from graph_data_inspection_contract import CONTROLLER as GRAPH_DATA_CONTROLLER, OPERATION as GRAPH_DATA_OPERATION, validate_contract as validate_graph_data_contract

EXECUTION_CLASSES = {"native_image_build", "source_inventory", "data_integrity", "oracle_screen", "witness_check", "repair_regression", "native_task_control"}
HELD_JOBS = {"ad-overlap", "coq-output", "native-codec"}
APPROVED_OPERATIONS = {
    VRPTW_ENVIRONMENT_OPERATION: "native_task_control",
    SOL_PROTOCOL_V7_OPERATION: "native_task_control",
    GRAPH_DATA_OPERATION: "data_integrity",
    VRPTW_DIAGNOSTIC_OPERATION: "native_task_control",
    VRPTW_OPERATION: "native_task_control",
    "graph-retained-reconstruction-v1": "native_task_control",
    SOL_AUDIT_V2_OPERATION: "native_task_control",
    "apple-resource-no-bytecode-build-sol-v1": "native_task_control",
    SOL_AUDIT_OPERATION: "native_task_control",
    "tree-t2-alias-correction-before-after-v1": "native_task_control",
    "apple-resource-integration-sol-v1": "native_task_control",
    "graph-reproduction-preservation-v1": "native_task_control",
    "tree-t2-arithmetic-native-v1": "native_task_control",
    "apple-resource-integration-v3": "native_task_control",
    "equivalence-t3-retained-reconstruction-v1": "native_task_control",
    "molecular-endpoint-controls-v1": "native_task_control",
    "apple-resource-integration-v2": "native_task_control",
    "molecular-harness-staging-compatibility-v1": "native_task_control",
    "molecular-harness-sysconfig-origin-v1": "native_task_control",
    "equivalence-t3-image-preservation-v1": "native_task_control",
    "molecular-harness-origin-diagnostics-v1": "native_task_control",
    "molecular-harness-generated-origin-v1": "native_task_control",
    "molecular-harness-startup-diagnostic-v1": "native_task_control",
    "molecular-harness-integration-v1": "native_task_control",
    "schemathesis-response-unit-v2": "native_task_control",
    "wireless-lineage-fresh-v2": "native_task_control",
    "apple-fixed-policies-v2": "native_task_control",
    "apple-fixed-policies-v1": "native_task_control",
    "apple-finite-scan-v2": "native_task_control",
    "apple-data-gap-v1": "native_task_control",
    "schemathesis-response-unit-v1": "native_task_control",
    "wireless-full-corpus-controls-v1": "native_task_control",
    "graph-astra-two-submission-replay-v1": "native_task_control",
    "equivalence-t3-overlay-integration-v1": "native_task_control",
    "treant-native-controls-v2": "native_task_control",
    "treant-source-acquisition-v1": "source_inventory",
    "equivalence-t3-native-controls-v2": "native_task_control",
    "triangulation-native-controls-v1": "native_task_control",
    "wireless-native-controls-v1": "native_task_control",
    "e2b-lifetime-metadata-v1": "source_inventory",
    "astra-graph-agent-pilot-v1": "native_task_control",
    "graph-archive-history-v4": "native_task_control",
    "graph-archive-history-v3": "native_task_control",
    "graph-archive-history-v2": "native_task_control",
    "codex-account-astra-tool-smoke-v1": "native_task_control",
    "codex-account-auth-smoke-v1": "native_task_control",
    "dcss-native-image-build-v1": "native_image_build",
    "dcss-native-gameplay-v1": "native_task_control",
    "graph-native-controls-v1": "native_task_control",
    "systems-schemathesis-baseline-v1": "native_task_control",
    "systems-metrics-component-v1": "native_task_control",
    "systems-metrics-identity-repair-v1": "native_task_control",
    "systems-metrics-full-scorer-v1": "native_task_control",
    "vliw-benign-capability-v1": "native_task_control",
    "vliw-image-metadata-v1": "native_task_control",
    "vliw-image-build-v1": "native_task_control",
    "vliw-image-build-portable-v2": "native_task_control",
    "vliw-config-diagnostic-v1": "native_task_control",
    "vliw-copy-image-lineage-v1": "native_task_control",
    "molecular-native-controls-v1": "native_task_control",
    "molecular-rounding-comparison-v1": "native_task_control",
    "molecular-data-dynamics-v1": "native_task_control",
    "molecular-content-origin-v1": "source_inventory",
    "original-file-preflight-v1": "source_inventory",
    "original-file-preflight-eight-v1": "source_inventory",
    "lean-disk-preflight-v1": "native_task_control",
    "lean-nf-capped-controls-v1": "native_task_control",
    "lean-confinement-diagnostic-v1": "native_task_control",
    "lean-confinement-binfmt-diagnostic-v2": "native_task_control",
    "lean-confinement-mountids-diagnostic-v3": "native_task_control",
    "lean-confinement-libmount-debug-v1": "native_task_control",
    "borden-native-controls-v1": "native_task_control",
    "cta-accounting-v1": "native_task_control",
    "cta-preflight-v1": "native_task_control",
    "cta-observed-accounting-v1": "native_task_control",
    "smt-cvc5-oracle-shard-v1": "oracle_screen",
    "smt-cvc5-high-memory-v1": "oracle_screen",
    "smt-z3-long-retry-v1": "oracle_screen",
    "smt-z3-memory-retry-v1": "oracle_screen",
    "smt-cvc5-long-retry-v1": "oracle_screen",
    "smt-cvc5-bootstrap-diagnostic-v1": "oracle_screen",
    "smt-cvc5-bootstrap-diagnostic-v2": "oracle_screen",
    "apple-native-controls-v1": "native_task_control",
    "apple-public-dynamics-v1": "native_task_control",
}
OPERATION_SUCCESS_STATUSES = {
    VRPTW_ENVIRONMENT_OPERATION: {"component_controls_completed_pending_independent_review"},
    SOL_PROTOCOL_V7_OPERATION: {"completed_protocol_collection_pending_review", "completed_protocol_collection_pending_actual_metadata_and_review"},
    GRAPH_DATA_OPERATION: {"data_observations_completed_pending_independent_review"},
    VRPTW_DIAGNOSTIC_OPERATION: {"component_controls_completed_pending_independent_review"},
    VRPTW_OPERATION: {"component_controls_completed_pending_independent_review"},
    "graph-retained-reconstruction-v1": {"retained_reconstruction_completed_pending_owned_worker_closure"},
    SOL_AUDIT_V2_OPERATION: {"completed_pending_private_and_independent_review", "completed_pending_actual_model_metadata_and_review"},
    "apple-resource-no-bytecode-build-sol-v1": {"completed_pending_independent_result_and_owned_worker_closure"},
    SOL_AUDIT_OPERATION: {"completed_pending_private_and_independent_review", "completed_pending_actual_model_metadata_and_review"},
    "tree-t2-alias-correction-before-after-v1": {"observed"},
    "apple-resource-integration-sol-v1": {"completed_pending_independent_result_and_owned_worker_closure"},
    "graph-reproduction-preservation-v1": {"preservation_replay_completed_pending_owned_worker_closure"},
    "apple-resource-integration-v3": {"completed_pending_independent_result_and_owned_worker_closure"},
    "equivalence-t3-retained-reconstruction-v1": {"observed"},
    "apple-resource-integration-v2": {"completed_pending_independent_result_and_owned_worker_closure"},
    "molecular-harness-staging-compatibility-v1": {"completed_pending_independent_result_and_owned_worker_closure"},
    "molecular-harness-sysconfig-origin-v1": {"completed_pending_independent_result_and_owned_worker_closure"},
    "molecular-harness-origin-diagnostics-v1": {"completed_pending_independent_result_and_owned_worker_closure"},
    "molecular-harness-generated-origin-v1": {"completed_pending_independent_result_and_owned_worker_closure"},
    "molecular-harness-startup-diagnostic-v1": {"completed_pending_independent_result_and_owned_worker_closure"},
    "molecular-harness-integration-v1": {"completed_pending_independent_result_and_owned_worker_closure"},
    "schemathesis-response-unit-v2": {"observed"},
    "wireless-lineage-fresh-v2": {"observed"},
    "apple-fixed-policies-v2": {"observed"},
    "apple-fixed-policies-v1": {"observed"},
    "apple-finite-scan-v2": {"observed"},
    "apple-data-gap-v1": {"observed"},
    "schemathesis-response-unit-v1": {"observed"},
    "wireless-full-corpus-controls-v1": {"observed"},
    "graph-astra-two-submission-replay-v1": {"replay_completed_pending_owned_worker_closure"},
    "equivalence-t3-image-preservation-v1": {"observed"},
    "equivalence-t3-overlay-integration-v1": {"observed"},
    "tree-t2-arithmetic-native-v1": {"observed"},
    "molecular-endpoint-controls-v1": {"observed"},
    "treant-native-controls-v2": {"observed"},
    "treant-source-acquisition-v1": {"selected_source_exported"},
    "equivalence-t3-native-controls-v2": {"observed"},
    "triangulation-native-controls-v1": {"observed"},
    "wireless-native-controls-v1": {"observed"},
    "e2b-lifetime-metadata-v1": {"observed"},
    "astra-graph-agent-pilot-v1": {"diagnostic_completed_pending_private_review"},
    "graph-archive-history-v4": {"completed_pending_owned_worker_closure"},
    "graph-archive-history-v3": {"completed_pending_owned_worker_closure"},
    "graph-archive-history-v2": {"completed_pending_owned_worker_closure"},
    "codex-account-astra-tool-smoke-v1": {"tool_smoke_succeeded"},
    "codex-account-auth-smoke-v1": {"inference_succeeded"},
    "dcss-native-image-build-v1": {"passed"},
    "dcss-native-gameplay-v1": {"completed"},
    "graph-native-controls-v1": {"passed"},
    "systems-schemathesis-baseline-v1": {"observed"},
    "systems-metrics-component-v1": {"observed"},
    "systems-metrics-identity-repair-v1": {"observed"},
    "systems-metrics-full-scorer-v1": {"observed"},
    "vliw-benign-capability-v1": {"completed"},
    "vliw-image-metadata-v1": {"completed"},
    "vliw-image-build-v1": {"completed"},
    "vliw-image-build-portable-v2": {"completed"},
    "vliw-config-diagnostic-v1": {"completed"},
    "vliw-copy-image-lineage-v1": {"completed"},
    "molecular-native-controls-v1": {"passed"},
    "molecular-rounding-comparison-v1": {"passed"},
    "molecular-data-dynamics-v1": {"passed"},
    "molecular-content-origin-v1": {"matched"},
    "original-file-preflight-v1": {"observed"},
    "original-file-preflight-eight-v1": {"observed"},
    "lean-disk-preflight-v1": {"passed"},
    "lean-nf-capped-controls-v1": {"observed"},
    "lean-confinement-diagnostic-v1": {"observed_capability"},
    "lean-confinement-binfmt-diagnostic-v2": {"observed_capability"},
    "lean-confinement-mountids-diagnostic-v3": {"observed_capability"},
    "lean-confinement-libmount-debug-v1": {"observed_capability"},
    "borden-native-controls-v1": {"passed"},
    "cta-accounting-v1": {"observed"},
    "cta-preflight-v1": {"observed"},
    "cta-observed-accounting-v1": {"observed"},
    "smt-cvc5-oracle-shard-v1": {"passed"},
    "smt-cvc5-high-memory-v1": {"passed"},
    "smt-z3-long-retry-v1": {"completed"},
    "smt-z3-memory-retry-v1": {"completed"},
    "smt-cvc5-long-retry-v1": {"completed"},
    "smt-cvc5-bootstrap-diagnostic-v1": {"completed"},
    "smt-cvc5-bootstrap-diagnostic-v2": {"completed"},
    "apple-native-controls-v1": {"passed"},
    "apple-public-dynamics-v1": {"passed"},
}
MAX_EXPORT_BYTES = 2 * 1024 * 1024
ASTRA_GRAPH_OPERATION = "astra-graph-agent-pilot-v1"
ASTRA_GRAPH_EXPORTS = {"result.json", "preparation.json", "pilot-artifacts.tar.gz"}
ASTRA_GRAPH_MAX_EXPORT_BYTES = 64 * 1024**2 + 2 * 128 * 1024
MAX_INPUT_BYTES = 16 * 1024 * 1024
MAX_JOB_SECONDS = 1200
ATTEMPT_RESERVE_USD = 0.1656  # One whole hour of the fixed worker, even for short jobs.
RESOURCE_PROFILES = {
    "small": {"max_input_bytes": 16 * 1024**2, "attempt_reserve_usd": .1656},
    "large": {"max_input_bytes": 32 * 1024**2, "attempt_reserve_usd": .5328},
}
SETTLEMENT_PROFILES = {
    'small': ('l9vwx8ash6vvnhj9dnx7', 2, 4096, 165600),
    'large': ('dqr9oryio6litwrml3gd', 8, 8192, 532800),
}
SETTLEMENT_POLICY = 'closed-lifecycle-plus-60s-round-minute-v1'


def _micro_usd(value):
    if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
        raise ValueError('Finite nonnegative accounting amount required')
    return int((Decimal(str(value)) * 1000000).to_integral_value(rounding=ROUND_CEILING))


def _accounting_json(path, limit):
    """Read only bounded ordinary proof files; never follow a symlink/FIFO."""
    if any(parent.is_symlink() for parent in (path, *path.parents)):
        raise ValueError('Accounting evidence cannot follow symlinks')
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_size > limit:
            raise ValueError('Accounting evidence must be a bounded regular file')
        raw = stream.read(limit + 1)
    if len(raw) > limit:
        raise ValueError('Accounting evidence exceeded its byte limit')
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('Duplicate accounting evidence key')
            result[key] = value
        return result
    value = json.loads(raw, object_pairs_hook=unique)
    canonical(value)  # Reject nonfinite values anywhere in the evidence.
    return value, digest(raw)


def _accounting_time(value):
    if not isinstance(value, str):
        raise ValueError('Accounting timestamp must be a timezone-aware string')
    parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if parsed.tzinfo is None:
        raise ValueError('Accounting timestamp lacks a timezone')
    return parsed.astimezone(timezone.utc)


def job_resources(job):
    name = job.get("resource_profile", "small")
    if name not in RESOURCE_PROFILES:
        raise ValueError("Unknown worker resource profile")
    large_operations = {"smt-cvc5-high-memory-v1", "smt-z3-memory-retry-v1", ASTRA_GRAPH_OPERATION}
    fs_large = (job.get("operation_id") == "deterministic-experiment-v1" and job.get("task_id") in ['flt_regular_formalization', 'sphere_eversion_formalization'] and {'e771c8308e359a38e86429182fb2d0efd485cd24e77088476ca65e0de94212a0': 'flt_regular_formalization', '1952baec0f3394afcb344d83f7ee5c73f3794c237af038f5b6a50cb39ad6c45d': 'sphere_eversion_formalization'}.get(hashlib.sha256(canonical(job)).hexdigest()) == job.get("task_id"))
    if name == "large" and job.get("operation_id") not in large_operations and not fs_large:
        raise ValueError("Large workers require an explicitly reviewed operation")
    if job.get("operation_id") in large_operations and name != "large":
        raise ValueError("This operation requires the pinned large profile")
    if job.get("operation_id") == "e2b-lifetime-metadata-v1":
        return {"max_input_bytes": 16 * 1024**2, "attempt_reserve_usd": .3381}
    return RESOURCE_PROFILES[name]


def timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def canonical(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def relative_path(value: str) -> str:
    if not isinstance(value, str) or not value or "\\" in value or "\x00" in value:
        raise ValueError("Invalid relative path")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in ("", "..", ".") for part in value.split("/")):
        raise ValueError("Path escapes or is not canonical")
    return value


GRAPH_RECONSTRUCTION_OPERATION = "graph-retained-reconstruction-v1"
GRAPH_RECONSTRUCTION_CONTROLLER = "graph-retained-reconstruction-owned-close-v1"
GRAPH_RECONSTRUCTION_PRIVATE_ROOT = "work/graph-preservation"
GRAPH_RECONSTRUCTION_INPUT = {'bytes': 92160, 'path': 'stage-a-v1/graph-preserve-replay-32f5208f376fcec0/eb097625e99046a680462dc382514b5e/image-artifact/candidate-image-delta.tar', 'sha256': 'e391f504ebae290bffef2412ebea94deb657a586d3b317a9e0e2a85923add414', 'storage': 'private_graph_retained_reconstruction', 'target': 'private-inputs/graph-derived-image-delta.tar'}


T3_RECONSTRUCTION_OPERATION = "equivalence-t3-retained-reconstruction-v1"
T3_RECONSTRUCTION_CONTROLLER = "equivalence-t3-reconstruct-owned-close-v1"
T3_RECONSTRUCTION_PRIVATE_ROOT = "work/image-deltas/t3-preservation-v1/equivalence-t3-preserve-e4126f44812c86b1/80af192dfa8d429da4a4491fb493140c/image-artifact/private"
T3_RECONSTRUCTION_INPUT = {"storage": "private_t3_reconstruction", "path": "t3-derived-image-delta.tar",
    "target": "private-inputs/t3-derived-image-delta.tar", "bytes": 40960,
    "sha256": "d0abe357316a95e80c143684ae054b255734462d462a04afc01fe156b641c1c4"}


GRAPH_REPLAY_OPERATION = "graph-astra-two-submission-replay-v1"
GRAPH_REPLAY_CONTROLLER = "graph-replay-private-input-v1"
GRAPH_PRESERVATION_OPERATION = "graph-reproduction-preservation-v1"
GRAPH_PRESERVATION_CONTROLLER = "graph-reproduction-preservation-owned-close-v1"
GRAPH_PRIVATE_CONTROLLERS = {GRAPH_REPLAY_OPERATION: GRAPH_REPLAY_CONTROLLER,
                             GRAPH_PRESERVATION_OPERATION: GRAPH_PRESERVATION_CONTROLLER}
GRAPH_REPLAY_INPUTS = {
    "agent-1.tar.gz": {"target": "private-inputs/agent-1.tar.gz", "bytes": 1702,
        "sha256": "1da8c341ef117b55c9450f646013889276c6877342ac7470e331ae8fc72b0f33"},
    "agent-2.tar.gz": {"target": "private-inputs/agent-2.tar.gz", "bytes": 2090,
        "sha256": "8a4c9d1ca8c324a89c856a0ff370b815b1472ec6390f08faecf2b629c991d8a5"},
}


def validate_job(job: dict, root: Path, *, private_root: Path | None = None, controller_id: str | None = None) -> dict[str, bytes]:
    input_limit = job_resources(job)["max_input_bytes"]
    if job.get("schema_version") != 1 or not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,95}", job.get("job_id", "")):
        raise ValueError("Invalid job identity")
    if job.get("execution_class") not in EXECUTION_CLASSES:
        raise ValueError("Undeclared execution class")
    if job.get("held_probe") or any(token in job["job_id"].replace("_", "-") for token in HELD_JOBS):
        raise ValueError("Held probes cannot enter this runner")
    if APPROVED_OPERATIONS.get(job.get("operation_id")) != job["execution_class"]:
        raise ValueError("Operation needs explicit reviewed registration")
    if job.get("status") != "ready" or job.get("certification_effect") != "none":
        raise ValueError("Only explicitly ready, noncertifying jobs may run")
    seconds = job.get("timeout_seconds")
    if type(seconds) is not int or not 1 <= seconds <= MAX_JOB_SECONDS:
        raise ValueError("Invalid job timeout")
    argv = job.get("argv")
    if not isinstance(argv, list) or not argv or any(not isinstance(x, str) or "\x00" in x for x in argv):
        raise ValueError("Explicit command argv required")
    if not job.get("acceptance") or not job.get("quality_scope"):
        raise ValueError("Missing outcome scope")
    if job.get("network_class") not in {"none", "pinned_public_image_acquisition", "pinned_public_oracle_acquisition", "account_authenticated_model", "public_image_and_wheel_bootstrap"}:
        raise ValueError("Undeclared network scope")
    if job.get("network_class") == "public_image_and_wheel_bootstrap" and job.get("operation_id") not in {"graph-archive-history-v2", "graph-archive-history-v3", "graph-archive-history-v4", GRAPH_REPLAY_OPERATION, GRAPH_PRESERVATION_OPERATION, GRAPH_RECONSTRUCTION_OPERATION, "molecular-harness-integration-v1", "molecular-harness-startup-diagnostic-v1", "molecular-harness-generated-origin-v1", "molecular-harness-origin-diagnostics-v1", "molecular-harness-sysconfig-origin-v1", "molecular-harness-staging-compatibility-v1", "apple-resource-integration-v2", "apple-resource-integration-v3", "apple-resource-integration-sol-v1", "apple-resource-no-bytecode-build-sol-v1"}:
        raise ValueError("Combined image and wheel bootstrap is limited to the reviewed graph operation")
    if job.get("network_class") == "account_authenticated_model" and job.get("operation_id") not in {"codex-account-auth-smoke-v1", "codex-account-astra-tool-smoke-v1", ASTRA_GRAPH_OPERATION, SOL_AUDIT_OPERATION, SOL_AUDIT_V2_OPERATION, SOL_PROTOCOL_V7_OPERATION}:
        raise ValueError("Account authentication requires an explicitly reviewed operation")
    if job.get("operation_id") == SOL_PROTOCOL_V7_OPERATION:
        if controller_id != SOL_PROTOCOL_V7_CONTROLLER:
            raise ValueError("Sol protocol V7 requires exact owned-close controller")
        validate_sol_protocol_v7_contract(job)
    if job.get("operation_id") == VRPTW_ENVIRONMENT_OPERATION:
        if controller_id != VRPTW_ENVIRONMENT_CONTROLLER:
            raise ValueError("VRPTW environment correction requires exact owned-close controller")
        validate_vrptw_environment_contract(job)
    if job.get("operation_id") == GRAPH_DATA_OPERATION:
        if controller_id != GRAPH_DATA_CONTROLLER:
            raise ValueError("Graph data requires exact private-auditor owned-close controller")
        validate_graph_data_contract(job)
    if job.get("operation_id") == VRPTW_DIAGNOSTIC_OPERATION:
        if controller_id != VRPTW_DIAGNOSTIC_CONTROLLER:
            raise ValueError("VRPTW diagnostic requires exact owned-close controller")
        validate_vrptw_diagnostic_contract(job)
    if job.get("operation_id") == VRPTW_OPERATION:
        if controller_id != VRPTW_CONTROLLER:
            raise ValueError("VRPTW requires exact owned-close controller")
        validate_vrptw_contract(job)
    if job.get("operation_id") == SOL_AUDIT_V2_OPERATION:
        if controller_id != SOL_AUDIT_V2_CONTROLLER:
            raise ValueError("Sol audit v2 requires its reviewed owned-close controller")
        validate_sol_audit_v2_contract(job)
    if job.get("operation_id") == SOL_AUDIT_OPERATION:
        if controller_id != SOL_AUDIT_CONTROLLER:
            raise ValueError("Sol audit requires its reviewed owned-close controller")
        validate_sol_audit_contract(job)
    if job.get("operation_id") == ASTRA_GRAPH_OPERATION:
        if (job.get("task_id") != "graph_node_classification"
                or job.get("network_class") != "account_authenticated_model"
                or job.get("private_exports") != ["pilot-artifacts.tar.gz"]):
            raise ValueError("Astra graph pilot requires its task, account scope and private archive declaration")
    if job.get("operation_id") == "graph-archive-history-v4":
        # Generic dispatch does not implement the two independently bounded routes.
        if (controller_id != "graph-v4-private-export-v1"
                or job.get("task_id") != "graph_node_classification"
                or job.get("network_class") != "public_image_and_wheel_bootstrap"
                or job.get("resource_profile") != "small"
                or job.get("worker_cpu") != 2 or job.get("worker_memory_mib") != 4096
                or job.get("timeout_seconds") != 1200
                or job.get("exports") != ["result.json", "integration-failure.log"]
                or job.get("private_exports") != ["integration-failure.log"]
                or job.get("max_export_bytes") != 196608):
            raise ValueError("Graph v4 requires its dedicated private-export controller and frozen envelope")
    if job.get("operation_id") == GRAPH_PRESERVATION_OPERATION:
        if (controller_id != GRAPH_PRESERVATION_CONTROLLER
                or job.get("task_id") != "graph_node_classification"
                or job.get("network_class") != "public_image_and_wheel_bootstrap"
                or job.get("resource_profile") != "small"
                or type(job.get("worker_cpu")) is not int or job["worker_cpu"] != 2
                or type(job.get("worker_memory_mib")) is not int or job["worker_memory_mib"] != 4096
                or job.get("timeout_seconds") != 1200
                or job.get("exports") != ["result.json", "integration-failure.log", "candidate-image-delta.tar", "paired-reports.tar"]
                or job.get("private_exports") != ["integration-failure.log", "candidate-image-delta.tar", "paired-reports.tar"]
                or job.get("max_export_bytes") != 18153472
                or job.get("argv") != ["python3", "-I", "-S", "-B", "worker.py", "--job-root", ".",
                                      "--input", "job.json", "--output", "result.json"]):
            raise ValueError("Graph preservation requires its exact private-input/export controller and frozen envelope")
    if job.get("operation_id") == GRAPH_REPLAY_OPERATION:
        if (controller_id != GRAPH_REPLAY_CONTROLLER
                or job.get("task_id") != "graph_node_classification"
                or job.get("network_class") != "public_image_and_wheel_bootstrap"
                or job.get("resource_profile") != "small"
                or type(job.get("worker_cpu")) is not int or job["worker_cpu"] != 2
                or type(job.get("worker_memory_mib")) is not int or job["worker_memory_mib"] != 4096
                or job.get("timeout_seconds") != 1200
                or job.get("exports") != ["result.json", "integration-failure.log"]
                or job.get("private_exports") != ["integration-failure.log"]
                or job.get("max_export_bytes") != 196608
                or job.get("argv") != ["python3", "-I", "-S", "-B", "worker.py", "--job-root", ".",
                                      "--input", "job.json", "--output", "result.json"]):
            raise ValueError("Graph replay requires its dedicated private-input controller and frozen envelope")
    if job.get("operation_id") == "treant-source-acquisition-v1":
        if (controller_id != "treant-source-private-export-v1"
                or job.get("task_id") != "treant_forest"
                or job.get("network_class") != "pinned_public_image_acquisition"
                or job.get("resource_profile") != "small"
                or job.get("worker_cpu") != 2 or job.get("worker_memory_mib") != 4096
                or job.get("timeout_seconds") != 330
                or job.get("exports") != ["acquisition/exports/result.json", "acquisition/exports/treant-selected-source.tar.gz"]
                or job.get("private_exports") != ["acquisition/exports/treant-selected-source.tar.gz"]
                or job.get("max_export_bytes") != 2752512):
            raise ValueError("Treant source acquisition requires its exact private-export controller and envelope")
    if job.get("operation_id") == "tree-t2-alias-correction-before-after-v1":
        if (controller_id != "tree-t2-alias-owned-close-v1"
                or job.get("task_id") != "tree_block_partitioning"
                or job.get("network_class") != "pinned_public_image_acquisition"
                or job.get("resource_profile") != "small"
                or job.get("worker_cpu") != 2 or job.get("worker_memory_mib") != 4096
                or job.get("resource_envelope", {}).get("worker_cpu") != 2
                or job.get("resource_envelope", {}).get("worker_memory_mib") != 4096
                or job.get("timeout_seconds") != 1200
                or job.get("exports") != ["result.json"] or job.get("private_exports")
                or job.get("max_export_bytes") != 131072
                or job.get("argv") != ["python3", "-B", "runner.py", "--job-root", ".", "--input", "job.json", "--output", "result.json"]):
            raise ValueError("Tree T2 alias comparison requires their bounded-collection owned-close controller")
    if job.get("operation_id") == "tree-t2-arithmetic-native-v1":
        if (controller_id != "tree-t2-owned-close-v1"
                or job.get("task_id") != "tree_block_partitioning"
                or job.get("network_class") != "pinned_public_image_acquisition"
                or job.get("resource_profile") != "small"
                or job.get("worker_cpu") != 2 or job.get("worker_memory_mib") != 4096
                or job.get("resource_envelope", {}).get("worker_cpu") != 2
                or job.get("resource_envelope", {}).get("worker_memory_mib") != 4096
                or job.get("timeout_seconds") != 1200
                or job.get("exports") != ["result.json"] or job.get("private_exports")
                or job.get("max_export_bytes") != 131072
                or job.get("argv") != ["python3", "-B", "runner.py", "--job-root", ".", "--input", "job.json", "--output", "result.json"]):
            raise ValueError("Tree T2 controls require their bounded-collection owned-close controller")
    if job.get("operation_id") == "molecular-endpoint-controls-v1":
        if (controller_id != "molecular-endpoint-owned-close-v1"
                or job.get("task_id") != "molecular_self_assembly"
                or job.get("network_class") != "pinned_public_image_acquisition"
                or job.get("resource_profile") != "small"
                or job.get("worker_cpu") != 2 or job.get("worker_memory_mib") != 4096
                or job.get("resource_envelope", {}).get("worker_cpu") != 2
                or job.get("resource_envelope", {}).get("worker_memory_mib") != 4096
                or job.get("timeout_seconds") != 1200
                or job.get("exports") != ["result.json"] or job.get("private_exports")
                or job.get("max_export_bytes") != 131072
                or job.get("argv") != ["python3", "-B", "runner.py", "--job-root", ".", "--input", "job.json", "--output", "result.json"]):
            raise ValueError("Molecular endpoint controls require their bounded-collection owned-close controller")
    if job.get("operation_id") == "treant-native-controls-v2":
        if (controller_id != "treant-native-owned-close-v3"
                or job.get("task_id") != "treant_forest"
                or job.get("network_class") != "pinned_public_image_acquisition"
                or job.get("resource_profile") != "small"
                or job.get("resource_envelope", {}).get("worker_cpu") != 2
                or job.get("resource_envelope", {}).get("worker_memory_mib") != 4096
                or job.get("timeout_seconds") != 1200
                or job.get("exports") != ["result.json"] or job.get("private_exports")
                or job.get("max_export_bytes") != 262144):
            raise ValueError("Treant native controls require their bounded-collection owned-close controller")
    if job.get("operation_id") == GRAPH_RECONSTRUCTION_OPERATION:
        if (controller_id != GRAPH_RECONSTRUCTION_CONTROLLER
                or job.get("task_id") != "graph_node_classification"
                or job.get("network_class") != "public_image_and_wheel_bootstrap"
                or job.get("resource_profile") != "small"
                or type(job.get("worker_cpu")) is not int or job["worker_cpu"] != 2
                or type(job.get("worker_memory_mib")) is not int or job["worker_memory_mib"] != 4096
                or job.get("timeout_seconds") != 1200
                or job.get("exports") != ["result.json", "integration-failure.log", "paired-reports.tar"]
                or job.get("private_exports") != ["integration-failure.log", "paired-reports.tar"]
                or job.get("max_export_bytes") != 17104896
                or job.get("argv") != ["python3", "-I", "-S", "-B", "worker.py", "--job-root", ".", "--input", "job.json", "--output", "result.json"]):
            raise ValueError("Graph retained reconstruction requires its exact private-input owned-close controller")
    if job.get("operation_id") == T3_RECONSTRUCTION_OPERATION:
        if (controller_id != T3_RECONSTRUCTION_CONTROLLER
                or job.get("task_id") != "equivalence_class_divide_and_conquer"
                or job.get("network_class") != "pinned_public_image_acquisition"
                or job.get("resource_profile") != "small"
                or job.get("resource_envelope", {}).get("worker_cpu") != 2
                or job.get("resource_envelope", {}).get("worker_memory_mib") != 4096
                or job.get("timeout_seconds") != 1200
                or job.get("exports") != ["result.json"] or job.get("private_exports")
                or job.get("max_export_bytes") != 131072
                or job.get("argv") != ["python3", "runner.py", "--job-root", ".", "--input", "job.json", "--output", "result.json"]):
            raise ValueError("T3 reconstruction requires its exact private-input owned-close controller")
    if job.get("operation_id") == "equivalence-t3-image-preservation-v1":
        if (controller_id != "equivalence-t3-image-preservation-owned-close-v1"
                or job.get("task_id") != "equivalence_class_divide_and_conquer"
                or job.get("network_class") != "pinned_public_image_acquisition"
                or job.get("resource_profile") != "small"
                or job.get("resource_envelope", {}).get("worker_cpu") != 2
                or job.get("resource_envelope", {}).get("worker_memory_mib") != 4096
                or job.get("timeout_seconds") != 1200
                or job.get("exports") != ["result.json", "private/t3-derived-image-delta.tar"]
                or job.get("private_exports") != ["private/t3-derived-image-delta.tar"]
                or job.get("max_export_bytes") != 1179648
                or job.get("argv") != ["python3", "runner.py", "--job-root", ".", "--input", "job.json", "--output", "result.json"]):
            raise ValueError("T3 image preservation requires its exact private-export owned-close controller")
    if job.get("operation_id") == "equivalence-t3-overlay-integration-v1":
        if (controller_id != "equivalence-t3-integration-owned-close-v1"
                or job.get("task_id") != "equivalence_class_divide_and_conquer"
                or job.get("network_class") != "pinned_public_image_acquisition"
                or job.get("resource_profile") != "small"
                or job.get("resource_envelope", {}).get("worker_cpu") != 2
                or job.get("resource_envelope", {}).get("worker_memory_mib") != 4096
                or job.get("timeout_seconds") != 1200
                or job.get("exports") != ["result.json"] or job.get("private_exports")
                or job.get("max_export_bytes") != 131072):
            raise ValueError("T3 evaluator integration controls require their bounded-collection owned-close controller")
    if job.get("operation_id") == "wireless-full-corpus-controls-v1":
        if (controller_id != "wireless-full-corpus-owned-close-v1"
                or job.get("task_id") != "wireless_electricity_layout"
                or job.get("network_class") != "pinned_public_image_acquisition"
                or job.get("resource_profile") != "small"
                or job.get("resource_envelope", {}).get("worker_cpu") != 2
                or job.get("resource_envelope", {}).get("worker_memory_mib") != 4096
                or job.get("timeout_seconds") != 1200
                or job.get("exports") != ["result.json"] or job.get("private_exports")
                or job.get("max_export_bytes") != 262144):
            raise ValueError("Wireless full-corpus controls require their bounded-collection owned-close controller")
    if job.get("operation_id") == "schemathesis-response-unit-v1":
        if (controller_id != "schemathesis-response-owned-close-v1"
                or job.get("task_id") != "schemathesis_config_modernization"
                or job.get("network_class") != "pinned_public_image_acquisition"
                or job.get("resource_profile") != "small"
                or job.get("resource_envelope", {}).get("worker_cpu") != 2
                or job.get("resource_envelope", {}).get("worker_memory_mib") != 4096
                or job.get("timeout_seconds") != 1200
                or job.get("exports") != ["result.json"] or job.get("private_exports")
                or job.get("max_export_bytes") != 131072):
            raise ValueError("Schemathesis Response pilot controls require their bounded-collection owned-close controller")
    if job.get("operation_id") == "wireless-lineage-fresh-v2":
        if (controller_id != "wireless-lineage-owned-close-v1"
                or job.get("task_id") != "wireless_electricity_layout"
                or job.get("network_class") != "pinned_public_image_acquisition"
                or job.get("resource_profile") != "small"
                or job.get("resource_envelope", {}).get("worker_cpu") != 2
                or job.get("resource_envelope", {}).get("worker_memory_mib") != 4096
                or job.get("timeout_seconds") != 1200
                or job.get("exports") != ["result.json"] or job.get("private_exports")
                or job.get("max_export_bytes") != 262144):
            raise ValueError("Wireless lineage/fresh controls require their bounded-collection owned-close controller")
    if job.get("operation_id") == "apple-fixed-policies-v2":
        if (controller_id != "apple-policy-owned-close-v2"
                or job.get("task_id") != "apple_incremental_game"
                or job.get("network_class") != "pinned_public_image_acquisition"
                or job.get("resource_profile") != "small"
                or job.get("resource_envelope", {}).get("worker_cpu") != 2
                or job.get("resource_envelope", {}).get("worker_memory_mib") != 4096
                or job.get("timeout_seconds") != 1200
                or job.get("exports") != ["result.json"] or job.get("private_exports")
                or job.get("max_export_bytes") != 262144):
            raise ValueError("Apple fixed-policy controls require their bounded-collection owned-close controller")
    if job.get("operation_id") == "apple-fixed-policies-v1":
        if (controller_id != "apple-policy-owned-close-v1"
                or job.get("task_id") != "apple_incremental_game"
                or job.get("network_class") != "pinned_public_image_acquisition"
                or job.get("resource_profile") != "small"
                or job.get("resource_envelope", {}).get("worker_cpu") != 2
                or job.get("resource_envelope", {}).get("worker_memory_mib") != 4096
                or job.get("timeout_seconds") != 1200
                or job.get("exports") != ["result.json"] or job.get("private_exports")
                or job.get("max_export_bytes") != 262144):
            raise ValueError("Apple fixed-policy controls require their bounded-collection owned-close controller")
    if job.get("operation_id") == "apple-finite-scan-v2":
        if (controller_id != "apple-finite-scan-owned-close-v2"
                or job.get("task_id") != "apple_incremental_game"
                or job.get("network_class") != "pinned_public_image_acquisition"
                or job.get("resource_profile") != "small"
                or job.get("resource_envelope", {}).get("worker_cpu") != 2
                or job.get("resource_envelope", {}).get("worker_memory_mib") != 4096
                or job.get("timeout_seconds") != 1200
                or job.get("exports") != ["result.json", "seed-hashes.jsonl"]
                or job.get("private_exports") != ["seed-hashes.jsonl"]
                or job.get("max_export_bytes") != 2359296):
            raise ValueError("Apple data-gap private-map controls require their bounded-collection owned-close controller")
    if job.get("operation_id") == "apple-data-gap-v1":
        if (controller_id != "apple-data-gap-owned-close-v2"
                or job.get("task_id") != "apple_incremental_game"
                or job.get("network_class") != "pinned_public_image_acquisition"
                or job.get("resource_profile") != "small"
                or job.get("resource_envelope", {}).get("worker_cpu") != 2
                or job.get("resource_envelope", {}).get("worker_memory_mib") != 4096
                or job.get("timeout_seconds") != 1200
                or job.get("exports") != ["result.json", "seed-hashes.jsonl"]
                or job.get("private_exports") != ["seed-hashes.jsonl"]
                or job.get("max_export_bytes") != 2359296):
            raise ValueError("Apple data-gap private-map controls require their bounded-collection owned-close controller")
    if job.get("operation_id") == "schemathesis-response-unit-v2":
        if (controller_id != "schemathesis-response-owned-close-v2"
                or job.get("task_id") != "schemathesis_config_modernization"
                or job.get("network_class") != "pinned_public_image_acquisition"
                or job.get("resource_profile") != "small"
                or job.get("resource_envelope", {}).get("worker_cpu") != 2
                or job.get("resource_envelope", {}).get("worker_memory_mib") != 4096
                or job.get("timeout_seconds") != 1200
                or job.get("exports") != ["result.json"] or job.get("private_exports")
                or job.get("max_export_bytes") != 131072):
            raise ValueError("Schemathesis Response pilot controls require their bounded-collection owned-close controller")
    if job.get("operation_id") == "molecular-harness-integration-v1":
        if (controller_id != "molecular-harness-owned-close-v1"
                or job.get("task_id") != "molecular_self_assembly"
                or job.get("network_class") != "public_image_and_wheel_bootstrap"
                or job.get("resource_profile") != "small"
                or job.get("resource_envelope", {}).get("worker_cpu") != 2
                or job.get("resource_envelope", {}).get("worker_memory_mib") != 4096
                or job.get("timeout_seconds") != 1200
                or job.get("exports") != ["result.json"] or job.get("private_exports")
                or job.get("max_export_bytes") != 262144
                or job.get("runtime_package_sha256") != "bec3941dedb70d094a301e94eae62bfb9eaeb6163ad4034f3cca957a77fc064e"
                or job.get("argv") != ["python3", "-I", "-S", "-B", "dispatch.py"]):
            raise ValueError("Molecular full-harness pilot requires its reviewed bounded-collection owned-close controller")
    if job.get("operation_id") == "molecular-harness-startup-diagnostic-v1":
        if (controller_id != "molecular-harness-startup-owned-close-v1"
                or job.get("task_id") != "molecular_self_assembly"
                or job.get("network_class") != "public_image_and_wheel_bootstrap"
                or job.get("resource_profile") != "small"
                or job.get("resource_envelope", {}).get("worker_cpu") != 2
                or job.get("resource_envelope", {}).get("worker_memory_mib") != 4096
                or job.get("timeout_seconds") != 1200
                or job.get("exports") != ["result.json"] or job.get("private_exports")
                or job.get("max_export_bytes") != 262144
                or job.get("runtime_package_sha256") != "fb91496f8c8cb8c2ba05b1c45e33f49fd6484cb15a0cfdc66237363980c1d8a9"
                or job.get("argv") != ["python3", "-I", "-S", "-B", "dispatch.py"]):
            raise ValueError("Molecular full-harness pilot requires its reviewed bounded-collection owned-close controller")
    if job.get("operation_id") == "molecular-harness-generated-origin-v1":
        if (controller_id != "molecular-harness-generated-origin-owned-close-v1"
                or job.get("task_id") != "molecular_self_assembly"
                or job.get("network_class") != "public_image_and_wheel_bootstrap"
                or job.get("resource_profile") != "small"
                or job.get("resource_envelope", {}).get("worker_cpu") != 2
                or job.get("resource_envelope", {}).get("worker_memory_mib") != 4096
                or job.get("timeout_seconds") != 1200
                or job.get("exports") != ["result.json"] or job.get("private_exports")
                or job.get("max_export_bytes") != 262144
                or job.get("runtime_package_sha256") != "b1956718936ff7f8c3aff7b4ec4a1962d1555e3acf095344ab12ed4fa0e303ff"
                or job.get("argv") != ["python3", "-I", "-S", "-B", "dispatch.py"]):
            raise ValueError("Molecular full-harness pilot requires its reviewed bounded-collection owned-close controller")
    if job.get("operation_id") == "molecular-harness-origin-diagnostics-v1":
        if (controller_id != "molecular-harness-origin-diagnostics-owned-close-v1"
                or job.get("task_id") != "molecular_self_assembly"
                or job.get("network_class") != "public_image_and_wheel_bootstrap"
                or job.get("resource_profile") != "small"
                or job.get("resource_envelope", {}).get("worker_cpu") != 2
                or job.get("resource_envelope", {}).get("worker_memory_mib") != 4096
                or job.get("timeout_seconds") != 1200
                or job.get("exports") != ["result.json"] or job.get("private_exports")
                or job.get("max_export_bytes") != 262144
                or job.get("runtime_package_sha256") != "b574bb826aae57a2f679012b54c14ad001267b09ffc8166e3bb2d947d4f8a098"
                or job.get("argv") != ["python3", "-I", "-S", "-B", "dispatch.py"]):
            raise ValueError("Molecular full-harness pilot requires its reviewed bounded-collection owned-close controller")
    if job.get("operation_id") == "molecular-harness-sysconfig-origin-v1":
        if (controller_id != "molecular-harness-sysconfig-origin-owned-close-v1"
                or job.get("task_id") != "molecular_self_assembly"
                or job.get("network_class") != "public_image_and_wheel_bootstrap"
                or job.get("resource_profile") != "small"
                or job.get("resource_envelope", {}).get("worker_cpu") != 2
                or job.get("resource_envelope", {}).get("worker_memory_mib") != 4096
                or job.get("timeout_seconds") != 1200
                or job.get("exports") != ["result.json"] or job.get("private_exports")
                or job.get("max_export_bytes") != 262144
                or job.get("runtime_package_sha256") != "1d687a196e41b7d806f94b2dac7b5d90879b061dc4263a8b93e3e6714151dd62"
                or job.get("argv") != ["python3", "-I", "-S", "-B", "dispatch.py"]):
            raise ValueError("Molecular full-harness pilot requires its reviewed bounded-collection owned-close controller")
    if job.get("operation_id") == "molecular-harness-staging-compatibility-v1":
        if (controller_id != "molecular-harness-staging-owned-close-v1"
                or job.get("task_id") != "molecular_self_assembly"
                or job.get("network_class") != "public_image_and_wheel_bootstrap"
                or job.get("resource_profile") != "small"
                or job.get("resource_envelope", {}).get("worker_cpu") != 2
                or job.get("resource_envelope", {}).get("worker_memory_mib") != 4096
                or job.get("timeout_seconds") != 1200
                or job.get("exports") != ["result.json"] or job.get("private_exports")
                or job.get("max_export_bytes") != 262144
                or job.get("runtime_package_sha256") != "07d750593648507dfe658cf0be76aecab61b6df73fe959e407739bdb7c483222"
                or job.get("argv") != ["python3", "-I", "-S", "-B", "dispatch.py"]):
            raise ValueError("Molecular full-harness pilot requires its reviewed bounded-collection owned-close controller")
    if job.get("operation_id") == "apple-resource-integration-v2":
        if (controller_id != "apple-resource-owned-close-v2"
                or job.get("task_id") != "apple_incremental_game"
                or job.get("network_class") != "public_image_and_wheel_bootstrap"
                or job.get("resource_profile") != "small"
                or job.get("resource_envelope", {}).get("worker_cpu") != 2
                or job.get("resource_envelope", {}).get("worker_memory_mib") != 4096
                or job.get("timeout_seconds") != 1200
                or job.get("exports") != ["result.json", "private/apple-derived-image-delta.tar"]
                or job.get("private_exports") != ["private/apple-derived-image-delta.tar"]
                or job.get("max_export_bytes") != 1310720
                or job.get("runtime_package_sha256") != "766940246737bce9f55a5d2d30e807ed90013dda1b77a7f546cb64fd12056e4b"
                or job.get("argv") != ["python3", "-I", "-S", "-B", "dispatch.py"]):
            raise ValueError("Apple resource integration requires its reviewed dual-export owned-close controller")
    if job.get("operation_id") == "apple-resource-integration-v3":
        if (controller_id != "apple-resource-owned-close-v3"
                or job.get("task_id") != "apple_incremental_game"
                or job.get("network_class") != "public_image_and_wheel_bootstrap"
                or job.get("resource_profile") != "small"
                or job.get("resource_envelope", {}).get("worker_cpu") != 2
                or job.get("resource_envelope", {}).get("worker_memory_mib") != 4096
                or job.get("timeout_seconds") != 1200
                or job.get("exports") != ["result.json", "private/apple-derived-image-delta.tar"]
                or job.get("private_exports") != ["private/apple-derived-image-delta.tar"]
                or job.get("max_export_bytes") != 1310720
                or job.get("runtime_package_sha256") != "da4b98b951bd04365ce2450998a8e4739198c6c0f9c4d95ee8def97777ca9c7f"
                or job.get("argv") != ["python3", "-I", "-S", "-B", "dispatch.py"]):
            raise ValueError("Apple resource integration requires its reviewed dual-export owned-close controller")
    if job.get("operation_id") == "apple-resource-integration-sol-v1":
        if (controller_id != "apple-resource-owned-close-sol-v1"
                or job.get("task_id") != "apple_incremental_game"
                or job.get("network_class") != "public_image_and_wheel_bootstrap"
                or job.get("resource_profile") != "small"
                or job.get("resource_envelope", {}).get("worker_cpu") != 2
                or job.get("resource_envelope", {}).get("worker_memory_mib") != 4096
                or job.get("timeout_seconds") != 1200
                or job.get("exports") != ["result.json", "private/apple-derived-image-delta.tar"]
                or job.get("private_exports") != ["private/apple-derived-image-delta.tar"]
                or job.get("max_export_bytes") != 1310720
                or job.get("runtime_package_sha256") != "c115591d139a1b0aa999bacd56ea11bf472d7393ac9e4de617cea3da80d1e749"
                or job.get("argv") != ["python3", "-I", "-S", "-B", "dispatch.py"]):
            raise ValueError("Apple resource integration requires its reviewed dual-export owned-close controller")
    if job.get("operation_id") == "apple-resource-no-bytecode-build-sol-v1":
        if (controller_id != "apple-resource-no-bytecode-owned-close-sol-v1"
                or job.get("task_id") != "apple_incremental_game"
                or job.get("network_class") != "public_image_and_wheel_bootstrap"
                or job.get("resource_profile") != "small"
                or job.get("resource_envelope", {}).get("worker_cpu") != 2
                or job.get("resource_envelope", {}).get("worker_memory_mib") != 4096
                or job.get("timeout_seconds") != 1200
                or job.get("exports") != ["result.json", "private/apple-derived-image-delta.tar"]
                or job.get("private_exports") != ["private/apple-derived-image-delta.tar"]
                or job.get("max_export_bytes") != 1310720
                or job.get("runtime_package_sha256") != "c6332ec913b73ae3639efa7248de49b2f1b80a8d820805e756a16ecfd3d8ac75"
                or job.get("argv") != ["python3", "-I", "-S", "-B", "dispatch.py"]):
            raise ValueError("Apple resource integration requires its reviewed dual-export owned-close controller")
    refs = job.get("inputs")
    if not isinstance(refs, list) or not refs:
        raise ValueError("Explicit hashed inputs required")
    root = root.resolve()
    graph_reconstruction_root = root.parent / GRAPH_RECONSTRUCTION_PRIVATE_ROOT
    if job.get("operation_id") == GRAPH_RECONSTRUCTION_OPERATION:
        if (private_root is None or Path(private_root).absolute() != graph_reconstruction_root
                or any(part.is_symlink() for part in (graph_reconstruction_root, *graph_reconstruction_root.parents))):
            raise ValueError("Graph retained reconstruction requires its exact ordinary private root")
        private_refs = [ref for ref in refs if isinstance(ref, dict) and ref.get("storage") == "private_graph_retained_reconstruction"]
        if (len(private_refs) != 1 or private_refs[0] != GRAPH_RECONSTRUCTION_INPUT
                or type(private_refs[0].get("bytes")) is not int):
            raise ValueError("Graph retained reconstruction requires its one exact accepted delta input")
    t3_private_root = root.parent / T3_RECONSTRUCTION_PRIVATE_ROOT
    if job.get("operation_id") == T3_RECONSTRUCTION_OPERATION:
        if (private_root is None or Path(private_root).absolute() != t3_private_root
                or any(part.is_symlink() for part in (t3_private_root, *t3_private_root.parents))):
            raise ValueError("T3 reconstruction requires its exact ordinary private root")
        private_refs = [ref for ref in refs if isinstance(ref, dict) and ref.get("storage") == "private_t3_reconstruction"]
        if (len(private_refs) != 1 or private_refs[0] != T3_RECONSTRUCTION_INPUT
                or type(private_refs[0].get("bytes")) is not int):
            raise ValueError("T3 reconstruction requires its one exact retained delta input")
    replay_private_root = root.parent / "work/cloud-queue/graph-replay-private-inputs/astra-v3"
    if job.get("operation_id") in GRAPH_PRIVATE_CONTROLLERS:
        if (private_root is None or Path(private_root).absolute() != replay_private_root
                or any(part.is_symlink() for part in (replay_private_root, *replay_private_root.parents))):
            raise ValueError("Graph replay requires its exact ordinary private root")
        private_refs = [ref for ref in refs if isinstance(ref, dict) and ref.get("storage") == "private_graph_replay"]
        if (len(private_refs) != 2 or {ref.get("path") for ref in private_refs} != set(GRAPH_REPLAY_INPUTS)):
            raise ValueError("Graph replay requires both exact retained submission inputs")
        for ref in private_refs:
            expected = GRAPH_REPLAY_INPUTS[ref["path"]]
            if (set(ref) != {"storage", "path", "target", "sha256", "bytes"}
                    or any(ref.get(key) != value for key, value in expected.items())
                    or type(ref["bytes"]) is not int):
                raise ValueError("Graph replay private input identity mismatch")
    payload = {}
    size = 0
    for ref in refs:
        input_root = root
        private_graph_reconstruction = ref.get("storage", "repo") == "private_graph_retained_reconstruction"
        if private_graph_reconstruction:
            if job.get("operation_id") != GRAPH_RECONSTRUCTION_OPERATION or controller_id != GRAPH_RECONSTRUCTION_CONTROLLER or private_root is None:
                raise ValueError("Graph retained private storage is limited to its dedicated reconstruction operation")
            input_root = graph_reconstruction_root
        elif job.get("operation_id") == GRAPH_RECONSTRUCTION_OPERATION and ref.get("target") == GRAPH_RECONSTRUCTION_INPUT["target"]:
            raise ValueError("Graph retained delta target must use its exact private storage slot")
        private_t3 = ref.get("storage", "repo") == "private_t3_reconstruction"
        if private_t3:
            if job.get("operation_id") != T3_RECONSTRUCTION_OPERATION or controller_id != T3_RECONSTRUCTION_CONTROLLER or private_root is None:
                raise ValueError("T3 private input storage is limited to its dedicated reconstruction operation")
            input_root = t3_private_root
        elif job.get("operation_id") == T3_RECONSTRUCTION_OPERATION and ref.get("target") == T3_RECONSTRUCTION_INPUT["target"]:
            raise ValueError("T3 retained delta target must use its private storage slot")
        private_graph = ref.get("storage", "repo") == "private_graph_replay"
        if private_graph:
            if job.get("operation_id") not in GRAPH_PRIVATE_CONTROLLERS or controller_id != GRAPH_PRIVATE_CONTROLLERS[job["operation_id"]] or private_root is None:
                raise ValueError("Graph private input storage is limited to its dedicated replay operation")
            input_root = replay_private_root
        elif job.get("operation_id") in GRAPH_PRIVATE_CONTROLLERS and ref.get("target") in {v["target"] for v in GRAPH_REPLAY_INPUTS.values()}:
            raise ValueError("Graph replay archive targets must use their private storage slots")
        elif ref.get("storage", "repo") == "private_smt":
            if job.get("operation_id") not in {"smt-cvc5-oracle-shard-v1", "smt-cvc5-high-memory-v1", "smt-z3-long-retry-v1", "smt-z3-memory-retry-v1", "smt-cvc5-long-retry-v1"} or private_root is None:
                raise ValueError("Private input root is available only to the reviewed SMT operation")
            input_root = Path(private_root).resolve()
        elif ref.get("storage", "repo") != "repo" and not private_t3 and not private_graph_reconstruction:
            raise ValueError("Unknown input storage")
        source = relative_path(ref["path"])
        target = relative_path(ref["target"])
        unresolved = input_root / source
        if any((input_root.joinpath(*PurePosixPath(source).parts[:i])).is_symlink()
               for i in range(1, len(PurePosixPath(source).parts) + 1)):
            raise ValueError("Input symlinks are not allowed")
        path = unresolved.resolve()
        path.relative_to(input_root)
        if target in payload or not re.fullmatch(r"[0-9a-f]{64}", ref.get("sha256", "")):
            raise ValueError("Duplicate input or missing identity")
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        with os.fdopen(fd, "rb") as stream:
            info = os.fstat(stream.fileno())
            if not stat.S_ISREG(info.st_mode) or info.st_size > input_limit:
                raise ValueError("Input must be a bounded regular file")
            if private_graph_reconstruction:
                expected = GRAPH_RECONSTRUCTION_INPUT
                if info.st_nlink != 1 or info.st_size != expected["bytes"]:
                    raise ValueError("Graph retained private delta must have its exact size and one link")
                data = stream.read(expected["bytes"] + 1)
                after = os.fstat(stream.fileno())
                if (len(data) != expected["bytes"] or
                        (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns) !=
                        (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns)):
                    raise ValueError("Graph retained private delta changed during read")
            elif private_t3:
                expected = T3_RECONSTRUCTION_INPUT
                if info.st_nlink != 1 or info.st_size != expected["bytes"]:
                    raise ValueError("T3 private delta must have its exact size and one link")
                data = stream.read(expected["bytes"] + 1)
                after = os.fstat(stream.fileno())
                if (len(data) != expected["bytes"] or
                        (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns) !=
                        (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns)):
                    raise ValueError("T3 private delta changed during read")
            elif private_graph:
                expected = GRAPH_REPLAY_INPUTS[source]
                if info.st_nlink != 1 or info.st_size != expected["bytes"]:
                    raise ValueError("Graph replay private input must have its exact size and one link")
                data = stream.read(expected["bytes"] + 1)
                after = os.fstat(stream.fileno())
                if (len(data) != expected["bytes"] or
                        (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns) !=
                        (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns)):
                    raise ValueError("Graph replay private input changed during read")
            else:
                data = stream.read(input_limit + 1)
        size += len(data)
        if size > input_limit or digest(data) != ref["sha256"]:
            raise ValueError("Input size or hash mismatch")
        payload[target] = data
    exports = job.get("exports")
    if not isinstance(exports, list) or not exports or len(exports) != len(set(exports)):
        raise ValueError("Explicit unique output allowlist required")
    for name in exports:
        relative_path(name)
    limit = job.get("max_export_bytes")
    export_bound = MAX_EXPORT_BYTES
    if job.get("operation_id") == SOL_PROTOCOL_V7_OPERATION:
        export_bound = 1179648
    if job.get("operation_id") == SOL_AUDIT_V2_OPERATION:
        export_bound = 8519680
    if job.get("operation_id") == SOL_AUDIT_OPERATION:
        export_bound = 8519680
    if job.get("operation_id") == ASTRA_GRAPH_OPERATION:
        if set(exports) != ASTRA_GRAPH_EXPORTS:
            raise ValueError("Astra graph pilot exports only two summaries and its private archive")
        export_bound = ASTRA_GRAPH_MAX_EXPORT_BYTES
    if job.get("operation_id") == "treant-source-acquisition-v1":
        export_bound = 2752512
    if job.get("operation_id") == "apple-finite-scan-v2":
        export_bound = 2359296
    if job.get("operation_id") == "apple-data-gap-v1":
        export_bound = 2359296
    if job.get("operation_id") == GRAPH_RECONSTRUCTION_OPERATION:
        export_bound = 17104896
    if job.get("operation_id") == GRAPH_PRESERVATION_OPERATION:
        export_bound = 18153472
    if type(limit) is not int or not 1 <= limit <= export_bound:
        raise ValueError("Invalid output bound")
    return payload


class QueueStore:
    """SQLite transactions prevent duplicate claims across coordinator processes."""

    def __init__(self, path: Path, ceiling_usd: float | None = 15.0):
        # Legacy callers retain their historical ceiling; renewed callers pass
        # the exact reviewed policy value explicitly, including None.
        if ceiling_usd is not None and (type(ceiling_usd) not in (int, float)
                or not math.isfinite(ceiling_usd) or not 0 < ceiling_usd <= 15):
            raise ValueError("Ceiling must be null or within the historical allowance")
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.ceiling = ceiling_usd
        with self.connect() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS jobs (
                    job_id TEXT PRIMARY KEY, manifest_sha TEXT NOT NULL,
                    manifest TEXT NOT NULL, state TEXT NOT NULL, attempt_id TEXT);
                CREATE TABLE IF NOT EXISTS attempts (
                    attempt_id TEXT PRIMARY KEY, job_id TEXT NOT NULL,
                    state TEXT NOT NULL, reserved_usd REAL NOT NULL,
                    created_at TEXT NOT NULL, result TEXT);
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, at TEXT NOT NULL,
                    job_id TEXT NOT NULL, attempt_id TEXT, event TEXT NOT NULL,
                    metadata TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS settlements (
                    attempt_id TEXT PRIMARY KEY, job_id TEXT NOT NULL,
                    original_reserved_microusd INTEGER NOT NULL,
                    estimated_cost_microusd INTEGER NOT NULL,
                    proof_sha256 TEXT NOT NULL, proof TEXT NOT NULL,
                    settled_at TEXT NOT NULL);
            """)

    def connect(self):
        db = sqlite3.connect(str(self.path), timeout=10)
        db.row_factory = sqlite3.Row
        return db

    @contextmanager
    def transaction(self):
        db = self.connect()
        try:
            db.execute("BEGIN IMMEDIATE")
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    @staticmethod
    def event(db, job_id, attempt_id, kind, metadata):
        db.execute("INSERT INTO events(at,job_id,attempt_id,event,metadata) VALUES(?,?,?,?,?)",
                    (timestamp(), job_id, attempt_id, kind, canonical(metadata).decode()))

    @staticmethod
    def _committed_micro(db):
        total = 0
        for row in db.execute(
                'SELECT a.*,j.manifest_sha,j.manifest,j.state AS job_state,j.attempt_id AS current_attempt,'
                's.estimated_cost_microusd,s.original_reserved_microusd,s.proof_sha256,s.proof '
                'FROM attempts a LEFT JOIN jobs j ON j.job_id=a.job_id '
                'LEFT JOIN settlements s ON s.attempt_id=a.attempt_id'):
            if row['manifest_sha'] is None:
                raise ValueError('Attempt lacks its current accounting job')
            original = _micro_usd(row['reserved_usd'])
            if row['estimated_cost_microusd'] is None:
                total += original
                continue
            cost = row['estimated_cost_microusd']
            proof = json.loads(row['proof'])
            if (type(cost) is not int or cost < 0 or row['original_reserved_microusd'] != original
                    or digest(canonical(proof)) != row['proof_sha256']
                    or proof.get('policy') != SETTLEMENT_POLICY
                    or proof.get('attempt_id') != row['attempt_id'] or proof.get('job_id') != row['job_id']
                    or proof.get('original_reserved_microusd') != original
                    or proof.get('estimated_cost_microusd') != cost
                    or proof.get('manifest_sha256') != row['manifest_sha']
                    or digest(canonical(json.loads(row['manifest']))) != row['manifest_sha']
                    or proof.get('result_sha256') != digest(canonical(json.loads(row['result'])))
                    or row['state'] not in {'completed', 'failed'} or row['job_state'] != row['state']
                    or row['current_attempt'] != row['attempt_id']):
                raise ValueError('Stored settlement no longer matches its immutable attempt proof')
            total += cost
        return total

    def register(self, job):
        encoded = canonical(job)
        identity = digest(encoded)
        with self.transaction() as db:
            old = db.execute("SELECT manifest_sha FROM jobs WHERE job_id=?", (job["job_id"],)).fetchone()
            if old is not None and old["manifest_sha"] != identity:
                raise ValueError("Job identity changed; use a new versioned job ID")
            if old is None:
                db.execute("INSERT INTO jobs VALUES(?,?,?,?,NULL)", (job["job_id"], identity, encoded.decode(), "pending"))
                self.event(db, job["job_id"], None, "registered", {"manifest_sha256": identity})
        return identity

    def claim(self, job_id, external_reserved_usd):
        if type(external_reserved_usd) not in (int, float) or not math.isfinite(external_reserved_usd) or external_reserved_usd < 0:
            raise ValueError("Fresh conservative external usage is required")
        with self.transaction() as db:
            row = db.execute("SELECT * FROM jobs WHERE job_id=?", (job_id,)).fetchone()
            if row is None or row["state"] != "pending":
                raise ValueError("Job is not pending; reconciliation or a distinct reviewed attempt is required")
            attempt_reserve = job_resources(json.loads(row["manifest"]))["attempt_reserve_usd"]
            committed = self._committed_micro(db)
            # Validate all cost amounts even when there is no aggregate cap.
            proposed_micro = committed + _micro_usd(external_reserved_usd) + _micro_usd(attempt_reserve)
            if self.ceiling is not None and proposed_micro > round(self.ceiling * 1000000):
                raise ValueError("Cloud compute ceiling would be exceeded")
            attempt = uuid.uuid4().hex
            db.execute("INSERT INTO attempts VALUES(?,?,?,?,?,NULL)", (attempt, job_id, "launch_intent", attempt_reserve, timestamp()))
            db.execute("UPDATE jobs SET state='launch_intent', attempt_id=? WHERE job_id=?", (attempt, job_id))
            self.event(db, job_id, attempt, "launch_intent", {"reserved_usd": attempt_reserve, "external_reserved_usd": external_reserved_usd})
            return attempt

    def mark_running(self, job_id, attempt_id, sandbox_id):
        with self.transaction() as db:
            row = db.execute("SELECT state,attempt_id FROM jobs WHERE job_id=?", (job_id,)).fetchone()
            if row is None or row["state"] != "launch_intent" or row["attempt_id"] != attempt_id:
                raise ValueError("Invalid running transition")
            db.execute("UPDATE jobs SET state='running' WHERE job_id=?", (job_id,))
            db.execute("UPDATE attempts SET state='running' WHERE attempt_id=?", (attempt_id,))
            self.event(db, job_id, attempt_id, "running", {"sandbox_id": sandbox_id})

    def finish(self, job_id, attempt_id, state, result):
        if state not in {"completed", "failed", "needs_reconciliation"}:
            raise ValueError("Invalid result state")
        if state == "completed" and (result.get("exports_verified") is not True or result.get("worker_termination_confirmed") is not True):
            raise ValueError("Completion needs passed declared checks, verified exports and confirmed cleanup")
        with self.transaction() as db:
            old = db.execute("SELECT state,attempt_id,manifest FROM jobs WHERE job_id=?", (job_id,)).fetchone()
            if old is None or old["attempt_id"] != attempt_id or old["state"] not in {"launch_intent", "running"}:
                raise ValueError("Invalid terminal transition")
            if state == "completed" and old["state"] != "running":
                raise ValueError("Completion requires a recorded execution transition")
            if state == "completed":
                operation = json.loads(old["manifest"])["operation_id"]
                if result.get("job_status") not in OPERATION_SUCCESS_STATUSES.get(operation, set()):
                    raise ValueError("Completion status does not match the reviewed operation")
            db.execute("UPDATE jobs SET state=? WHERE job_id=?", (state, job_id))
            db.execute("UPDATE attempts SET state=?,result=? WHERE attempt_id=?", (state, canonical(result).decode(), attempt_id))
            self.event(db, job_id, attempt_id, state, result)

    def settle_closed_attempt(self, attempt_id, *, expected_owner):
        """Apply an idempotent estimated-liability settlement, never invoice spend.

        Only exact terminal receipts and saved NotFound-confirmed worker closure
        qualify. Original reservations are immutable. Unknowns raise and keep
        their full hold. No provider call occurs. The provider shared lock is
        held through proof validation and the SQLite settlement transaction.
        """
        if not isinstance(attempt_id, str) or not re.fullmatch(r'[0-9a-f]{32}', attempt_id):
            raise ValueError('Exact attempt identifier required')
        if not isinstance(expected_owner, str) or not expected_owner.strip():
            raise ValueError('Explicit expected worker owner required')
        directory = self.path.parent
        lock_path = directory / 'provider/.cloud-workers.lock'
        if any(parent.is_symlink() for parent in (lock_path, *lock_path.parents)):
            raise ValueError('Provider accounting lock cannot follow symlinks')
        fd = os.open(lock_path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        try:
            if not stat.S_ISREG(os.fstat(fd).st_mode):
                raise ValueError('Provider accounting lock must be regular')
            fcntl.flock(fd, fcntl.LOCK_SH)
            provider, _ = _accounting_json(directory / 'provider/cloud-workers.json', 16 * 1024**2)
            receipt, receipt_sha = _accounting_json(directory / 'attempts' / f'{attempt_id}.json', 2 * 1024**2)
            with self.transaction() as db:
                attempt = db.execute('SELECT * FROM attempts WHERE attempt_id=?', (attempt_id,)).fetchone()
                if attempt is None or attempt['state'] not in {'completed', 'failed'} or not attempt['result']:
                    raise ValueError('Only a terminal known attempt can settle')
                job = db.execute('SELECT * FROM jobs WHERE job_id=?', (attempt['job_id'],)).fetchone()
                if job is None or job['attempt_id'] != attempt_id or job['state'] != attempt['state']:
                    raise ValueError('Current job and attempt identity/state differ')
                manifest, result = json.loads(job['manifest']), json.loads(attempt['result'])
                if digest(canonical(manifest)) != job['manifest_sha'] or manifest.get('job_id') != job['job_id']:
                    raise ValueError('Current manifest identity changed')
                registered = list(db.execute("SELECT metadata FROM events WHERE job_id=? AND event='registered'", (job['job_id'],)))
                if len(registered) != 1 or json.loads(registered[0]['metadata']).get('manifest_sha256') != job['manifest_sha']:
                    raise ValueError('Current manifest differs from immutable registration evidence')
                if canonical(receipt) != canonical(result) or result.get('attempt_id') != attempt_id or result.get('job_id') != job['job_id'] or result.get('worker_termination_confirmed') is not True:
                    raise ValueError('Exact receipt and literal closure confirmation required')
                terminal_events = list(db.execute('SELECT metadata FROM events WHERE attempt_id=? AND job_id=? AND event=?',
                                                  (attempt_id, job['job_id'], attempt['state'])))
                if len(terminal_events) != 1 or canonical(json.loads(terminal_events[0]['metadata'])) != canonical(result):
                    raise ValueError('Terminal receipt is not bound to its recorded event')
                token, sid = result.get('worker_reservation'), result.get('sandbox_id')
                if not isinstance(token, str) or not isinstance(sid, str) or not sid:
                    raise ValueError('Receipt lacks exact worker identity')
                records = provider.get('reservations', {})
                record = records.get(token, {})
                info = record.get('provider_info', {})
                if record.get('status') != 'closed' or record.get('owner') != expected_owner or record.get('creation_token') != token or record.get('sandbox_id') != sid:
                    raise ValueError('Worker lacks exact owned closed lifecycle')
                if info.get('sandbox_id') != sid or info.get('metadata', {}).get('owner') != expected_owner or info.get('metadata', {}).get('creation_token') != token:
                    raise ValueError('Provider identity does not match the receipt')
                worker_job = record.get('jobs', {}).get(job['job_id'], {})
                expected_inputs = {item['target']: 'sha256:' + item['sha256'] for item in manifest['inputs']}
                if len(expected_inputs) != len(manifest['inputs']) or worker_job.get('inputs') != expected_inputs or worker_job.get('remote_input_hashes_verified') is not True:
                    raise ValueError('Worker upload is not bound to exact manifest inputs')
                if worker_job.get('status') != 'command_completed' or type(worker_job.get('exit_code')) is not int or type(result.get('command_exit_code')) is not int or worker_job['exit_code'] != result['command_exit_code']:
                    raise ValueError('Worker command lifecycle differs from terminal receipt')
                argv = manifest.get('argv')
                if not isinstance(argv, list) or not argv or any(not isinstance(value, str) or '\x00' in value for value in argv):
                    raise ValueError('Manifest lacks an exact command argv')
                if worker_job.get('command_sha256') != 'sha256:' + digest(json.dumps(argv).encode()):
                    raise ValueError('Worker command is not bound to the manifest argv')
                if type(worker_job.get('timeout_seconds')) is not int or type(manifest.get('timeout_seconds')) is not int or worker_job['timeout_seconds'] != manifest['timeout_seconds']:
                    raise ValueError('Worker command timeout differs from its manifest')
                if sum(r.get('sandbox_id') == sid for r in records.values()) != 1:
                    raise ValueError('Worker is attributed to multiple reservations')
                for other in db.execute('SELECT result FROM attempts WHERE attempt_id<>? AND result IS NOT NULL', (attempt_id,)):
                    prior = json.loads(other['result'])
                    if prior.get('worker_reservation') == token or prior.get('sandbox_id') == sid:
                        raise ValueError('Worker is attributed to multiple attempts')
                name = manifest.get('resource_profile', 'small')
                resources = job_resources(manifest)
                template, cpu, memory, rate = SETTLEMENT_PROFILES[name]
                if record.get('resource_profile', 'small') != name or record.get('template_id') != template:
                    raise ValueError('Pinned worker and manifest profiles differ')
                for field, expected in [('cpu_count', cpu), ('memory_mb', memory)]:
                    if ('resource_profile' in record or field in record) and (type(record.get(field)) is not int or record[field] != expected):
                        raise ValueError('Pinned allocation differs from selected profile')
                    if type(info.get(field)) is not int or info[field] != expected:
                        raise ValueError('Provider allocation differs from selected profile')
                original = _micro_usd(attempt['reserved_usd'])
                reserve_seconds = 7350 if manifest.get('operation_id') == 'e2b-lifetime-metadata-v1' else 3600
                expected_reserve = (rate * reserve_seconds + 3599) // 3600
                if info.get('template_id') != template or original != expected_reserve or _micro_usd(resources['attempt_reserve_usd']) != expected_reserve:
                    raise ValueError('Template or original rate differs from selected profile')
                requested, started, closed, claimed = map(_accounting_time,
                    (record.get('requested_at'), info.get('started_at'), record.get('closed_at'), attempt['created_at']))
                begin = min(requested, started, claimed)
                duration = closed - begin
                elapsed_us = (duration.days * 86400 + duration.seconds) * 1000000 + duration.microseconds
                if closed < max(requested, started, claimed) or elapsed_us > 86400 * 1000000 or (closed - datetime.now(timezone.utc)).total_seconds() > 60:
                    raise ValueError('Lifecycle timestamps are reversed, future or outside the 24-hour accounting bound')
                if (requested - claimed).total_seconds() > 60 or (claimed - started).total_seconds() > 60:
                    raise ValueError('Reservation, claim and provider creation ordering differs')
                command_started, command_finished = map(_accounting_time, (worker_job.get('started_at'), worker_job.get('finished_at')))
                if not max(requested, started, claimed) <= command_started <= command_finished <= closed:
                    raise ValueError('Command timestamps contradict worker creation/closure lifecycle')
                charged_seconds = ((elapsed_us + 60 * 1000000 + 60 * 1000000 - 1) // (60 * 1000000)) * 60
                cost = (rate * charged_seconds + 3599) // 3600
                proof = {'policy': SETTLEMENT_POLICY, 'attempt_id': attempt_id, 'job_id': job['job_id'],
                         'manifest_sha256': job['manifest_sha'], 'receipt_sha256': receipt_sha,
                         'result_sha256': digest(canonical(result)),
                         'provider_record_sha256': digest(canonical(record)), 'worker_reservation': token,
                         'sandbox_id': sid, 'owner': expected_owner, 'resource_profile': name,
                         'template_id': template, 'cpu_count': cpu, 'memory_mb': memory,
                         'hourly_rate_microusd': rate, 'original_reserved_microusd': original,
                         'estimated_cost_microusd': cost, 'requested_at': record['requested_at'],
                         'provider_started_at': info['started_at'], 'attempt_created_at': attempt['created_at'],
                         'closure_observed_at': record['closed_at'], 'charged_seconds': charged_seconds,
                         'command_started_at': worker_job['started_at'], 'command_finished_at': worker_job['finished_at'],
                         'command_sha256': worker_job['command_sha256'],
                         'closure_basis': 'Saved closed status emitted after provider NotFound plus exact terminal receipt confirmation; no new provider call.'}
                identity = digest(canonical(proof))
                existing = db.execute('SELECT * FROM settlements WHERE attempt_id=?', (attempt_id,)).fetchone()
                if existing is not None:
                    if existing['proof_sha256'] != identity or existing['proof'] != canonical(proof).decode() or existing['estimated_cost_microusd'] != cost or existing['original_reserved_microusd'] != original:
                        raise ValueError('Existing settlement differs from current proof')
                    return dict(proof, settlement_status='already_settled', proof_sha256=identity)
                db.execute('INSERT INTO settlements VALUES(?,?,?,?,?,?,?)',
                           (attempt_id, job['job_id'], original, cost, identity, canonical(proof).decode(), timestamp()))
                self.event(db, job['job_id'], attempt_id, 'estimated_liability_settled', proof)
                return dict(proof, settlement_status='settled', proof_sha256=identity)
        finally:
            os.close(fd)

    def snapshot(self):
        with self.connect() as db:
            jobs = [dict(row) for row in db.execute("SELECT job_id,manifest_sha,state,attempt_id FROM jobs ORDER BY job_id")]
            reserved = db.execute("SELECT COALESCE(SUM(reserved_usd),0) FROM attempts").fetchone()[0]
            committed = self._committed_micro(db) / 1000000
            settled = db.execute('SELECT COUNT(*) FROM settlements').fetchone()[0]
        return {"jobs": jobs, "conservatively_reserved_usd": reserved, "ceiling_usd": self.ceiling,
                "original_full_hour_reservations_usd": round(reserved, 6),
                "estimated_committed_usd": committed, "settled_attempt_count": settled,
                "estimated_headroom_before_external_reserve_usd": None if self.ceiling is None else round(self.ceiling - committed, 6),
                "accounting_scope": "Original full-hour reservations are cumulative historical holds, not current commitment. Validated closed-worker settlements adjust estimated liability, not invoice spend. A null ceiling/headroom records no agent-imposed spend cap. When bounded, subtract the exact current policy external reserve from headroom.",
                "certified_tasks": 0, "scope": "Job execution status only; no task release gate is set by this queue."}
