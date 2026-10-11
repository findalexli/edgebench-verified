#!/usr/bin/env python3
# Copyright (c) 2026 EdgeBench Verified contributors
# SPDX-License-Identifier: Apache-2.0
"""Prepare and execute the reviewed cloud audit queue without local workloads.

The first registered operation builds/inspects the DCSS candidate images. Other
tasks remain explicitly pending until their own controls are reviewed. E2B_API_KEY
is read locally by the SDK; it is never an input or a sandbox environment value.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import stat
import tempfile
import threading

try:
    from .cloud_queue import QueueStore, OPERATION_SUCCESS_STATUSES, canonical, digest, job_resources, relative_path, validate_job
    from .cloud_policy import read_policy
    from .cloud_dispatch_resources import STAGING_BUDGET
except ImportError:
    from cloud_queue import QueueStore, OPERATION_SUCCESS_STATUSES, canonical, digest, job_resources, relative_path, validate_job
    from cloud_policy import read_policy
    from cloud_dispatch_resources import STAGING_BUDGET

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "audit/cloud/queue-plan.json"
OWNER = "edgebenchverified-20261007-scaled-audit"
OWNERS = ("edgebenchverified-20261007-runtime-ad-o9qveecn", "edgebenchverified-20261007-runtime-ad-o9qveecn-artifact", OWNER)
AUDIT_STARTED_AT = "2026-10-08T04:35:48+00:00"
AUDIT_DEADLINE = "2026-10-10T05:18:55+00:00"


def private_input_root():
    return ROOT.parent / "work/smt-corpus-audit/queue-shards"


def load_job_reference(item):
    """Resolve only the two fixed audit stores, without publishing private jobs."""
    storage = item.get("storage", "repo")
    if storage not in {"repo", "private_smt"}:
        raise ValueError("Unknown job manifest storage")
    base = ROOT if storage == "repo" else private_input_root()
    name = relative_path(item["path"])
    path = base / name
    if any(parent.is_symlink() for parent in (path, *path.parents) if parent != base.parent):
        raise ValueError("Job manifest cannot follow symlinks")
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, "rb") as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_size > 1024**2:
            raise ValueError("Job manifest must be a bounded regular file")
        data = stream.read(1024**2 + 1)
    if len(data) > 1024**2 or digest(data) != item.get("sha256"):
        raise ValueError("Queue plan job hash or size mismatch")
    job = json.loads(data)
    if storage == "private_smt" and job.get("operation_id") not in {"smt-cvc5-oracle-shard-v1", "smt-cvc5-high-memory-v1", "smt-z3-long-retry-v1", "smt-z3-memory-retry-v1", "smt-cvc5-long-retry-v1"}:
        raise ValueError("Private manifests are restricted to SMT oracle shards")
    return job


def require_audit_time(timeout_seconds):
    remaining = (datetime.fromisoformat(AUDIT_DEADLINE) - datetime.now(timezone.utc)).total_seconds()
    if remaining < timeout_seconds + 300:
        raise ValueError("Audit time allowance cannot cover launch, execution and cleanup")


def external_leases():
    """Called under the shared lock; unknown legacy creation blocks new work."""
    try:
        from .cloud_worker import ExternalLease
    except ImportError:
        from cloud_worker import ExternalLease
    leases = []
    for name in ("e2b-pilot-state.json", "e2b-artifact-state.json"):
        path = ROOT.parent / "work/runtime-diagnosis" / name
        state = read(path)
        status = state.get("status", "")
        if status.startswith("killed_") or status == "closed":
            continue
        if status != "running" or not state.get("sandbox_id") or state.get("owner") not in OWNERS:
            raise ValueError("Legacy worker creation/status needs reconciliation")
        leases.append(ExternalLease(state["owner"], state["sandbox_id"]))
    return leases


@contextmanager
def lifecycle_lock():
    """Share the existing SMT controller's creation/rotation critical section."""
    path = ROOT.parent / "work/runtime-diagnosis/.e2b-lifecycle.lock"
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_CREAT | os.O_RDWR | os.O_CLOEXEC | os.O_NOFOLLOW, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        os.close(fd)


def read(path):
    return json.loads(path.read_text())


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n")


def freeze(path, data):
    """Atomically create immutable bytes without replacing an earlier package."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != data:
            raise ValueError("Frozen input changed")
        return
    fd, temporary = tempfile.mkstemp(prefix=".freeze-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data); stream.flush(); os.fsync(stream.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError:
            if path.read_bytes() != data:
                raise ValueError("Concurrent frozen input mismatch")
    finally:
        os.unlink(temporary)


def ref(path):
    return {"path": str(path.relative_to(ROOT)), "sha256": digest(path.read_bytes())}


def prepare():
    policy = read_policy()
    existing_jobs = read(PLAN).get("jobs", []) if PLAN.exists() else []
    build_path = ROOT / "candidates/build-plan.json"
    build_plan = read(build_path)
    dcss = next(item for item in build_plan["tasks"] if item["task_id"] == "dcss_dungeon_ai")
    driver = ROOT / "tools/cloud_jobs/dcss_build.py"
    job_template = {
        "schema_version": 1, "task_id": "dcss_dungeon_ai",
        "status": "ready", "operation_id": "dcss-native-image-build-v1",
        "execution_class": "native_image_build", "certification_effect": "none",
        "quality_scope": "Pinned-parent candidate image construction and installed evaluator identity; no game or model execution.",
        "network_class": "pinned_public_image_acquisition", "timeout_seconds": 1200,
        "argv": ["python3", "repo/tools/cloud_jobs/dcss_build.py", "--job-root", ".", "--input", "job.json", "--output", "result.json"],
        "exports": ["result.json"], "max_export_bytes": 2 * 1024**2,
        "acceptance": "Driver status passed, every allowed export hashed, and worker termination confirmed. No release gate is changed.",
    }
    config_template = {"schema_version": 1, "repo_root": "repo", "build_plan_sha256": digest(build_path.read_bytes()),
                       "deadline_seconds": 1200, "min_free_bytes": 5 * 1024**3}
    identity = digest(canonical({"build_plan": ref(build_path), "driver": ref(driver),
        "job": job_template, "config": config_template, "audit_deadline": AUDIT_DEADLINE,
        "external_reserve": policy["external_work_reserved_usd"]}))[:16]
    job_id = "dcss-image-build-" + identity
    package = ROOT / "audit/cloud/packages" / job_id
    inputs = []
    originals = [build_path, driver]
    originals += [ROOT / dcss[k]["path"] for k in ("source_manifest", "candidate_manifest", "overlay_provenance")]
    originals += [ROOT / item["path"] for build in dcss["builds"] for item in build["inputs"]]
    for source in sorted(set(originals)):
        target = "repo/" + str(source.relative_to(ROOT))
        destination = package / target
        data = source.read_bytes()
        freeze(destination, data)
        inputs.append(dict(ref(destination), target=target))
    job_input = dict(config_template, job_id=job_id)
    freeze(package / "job.json", (json.dumps(job_input, indent=2) + "\n").encode())
    inputs.append(dict(ref(package / "job.json"), target="job.json"))
    job = dict(job_template, job_id=job_id, inputs=inputs)
    validate_job(job, ROOT)
    job_path = ROOT / "audit/cloud/jobs" / f"{job_id}.json"
    if job_path.exists() and canonical(read(job_path)) != canonical(job):
        raise ValueError("Immutable job manifest changed")
    freeze(job_path, (json.dumps(job, indent=2) + "\n").encode())
    registry = read(ROOT / "audit/task-registry.json")
    plan = {
        "schema_version": 1, "scope": "All 51 public tasks accounted for; only reviewed operations enter execution.",
        "policy": {"max_workers_including_external_audit_jobs": policy["max_workers"], "cpu_per_worker": 2,
                   "memory_mib_per_worker": 4096, "initial_ttl_seconds": 1800,
                   "initial_compute_ceiling_usd": policy["compute_ceiling_usd"], "external_work_reserved_usd": policy["external_work_reserved_usd"],
                   "external_reserve_scope": "Exact versioned policy reserve; zero under later user steering. Per-job reservations and settlements remain recorded.",
                   "audit_started_at_utc": AUDIT_STARTED_AT, "audit_deadline_utc": AUDIT_DEADLINE,
                   "queue_per_attempt_reserve_usd": .1656, "automatic_retries": 0,
                   "held_operations": ["ad-overlap", "coq-output", "native-codec"]},
        "resource_policy": ref(ROOT / "audit/cloud/resource-policy.json"),
        "jobs": [ref(job_path)] + [item for item in existing_jobs if item.get("path") != str(job_path.relative_to(ROOT))],
        "tasks": [{"task_id": task_id, "automation_status": "reviewed_image_build_ready" if task_id == "dcss_dungeon_ai" else "task_specific_controls_pending",
                   "certified": False} for task_id in registry["task_ids"]],
    }
    save(PLAN, plan)
    return {"tasks_accounted_for": len(plan["tasks"]), "ready_jobs": len(plan["jobs"]), "certified_tasks": 0}


def execute_one(job, store, state_dir):
    with STAGING_BUDGET.load(lambda: validate_job(job, ROOT, private_root=private_input_root()),
                            max_payload_bytes=job_resources(job)["max_input_bytes"]) as staged:
        return _execute_staged(job, store, state_dir, staged)


def _execute_staged(job, store, state_dir, staged):
    try:
        from .cloud_worker import CapacityUnavailable, CloudWorkerManager, SDKProvider
    except ImportError:
        from cloud_worker import CapacityUnavailable, CloudWorkerManager, SDKProvider
    # Hash-check and bound every byte before making a cloud request.
    require_audit_time(job["timeout_seconds"])
    store.register(job)
    policy = read_policy()
    profile = job.get("resource_profile", "small")
    attempt = None
    worker = None
    manager = None
    token = None
    result = {"job_id": job["job_id"], "attempt_id": attempt,
              "execution_class": job["execution_class"], "certification_effect": "none",
              "exports_verified": False, "worker_termination_confirmed": False}
    terminal = "needs_reconciliation"
    try:
        manager = CloudWorkerManager(SDKProvider(profile=profile), state_dir / "provider", OWNERS, max_workers=policy["max_workers"], profile=profile,
            second_worker_reason="User authorized up to 50 cloud workers and larger resources where useful. The shared limit counts all known profiles and pending reservations; each attempt retains its profile's full hourly cost reservation and settlement accounting under the exact versioned spending policy.")
        with lifecycle_lock():
            require_audit_time(job["timeout_seconds"])
            if STAGING_BUDGET.snapshot()["admissions_stopped"]:
                return {"job_id": job["job_id"], "state": "dispatch_stopped", "certified_tasks": 0}
            try:
                token = manager.reserve(OWNER, external_leases=external_leases())
            except CapacityUnavailable:
                return {"job_id": job["job_id"], "state": "deferred_capacity", "certified_tasks": 0}
            result["worker_reservation"] = token
            try:
                attempt = store.claim(job["job_id"], policy["external_work_reserved_usd"])
            except ValueError:
                manager.cancel_reservation(token)
                return {"job_id": job["job_id"], "state": "deferred_claim_or_budget", "certified_tasks": 0}
            result["attempt_id"] = attempt
            worker = manager.create_reserved(token)
        result["sandbox_id"] = worker.sandbox_id
        receipt = worker.upload(job["job_id"], staged.payload, staged.expected_sha256,
                                max_bytes=job_resources(job)["max_input_bytes"])
        staged.verified_upload(receipt, job_id=job["job_id"])
        require_audit_time(job["timeout_seconds"])
        store.mark_running(job["job_id"], attempt, worker.sandbox_id)
        run = worker.run(job["job_id"], job["argv"], timeout_seconds=job["timeout_seconds"], export_margin_seconds=90)
        result["command_exit_code"] = run["exit_code"]
        destination = state_dir / "exports" / job["job_id"] / attempt
        exported = worker.download(job["job_id"], job["exports"], destination, max_bytes=job["max_export_bytes"])
        result["exports"] = exported
        result["exports_verified"] = True
        driver_result = read(destination / "result.json")
        if driver_result.get("job_id") != job["job_id"] or driver_result.get("task_id") != job["task_id"]:
            raise ValueError("Driver identity mismatch")
        result["job_status"] = driver_result.get("status")
        closed = worker.close("Job finished; compact allowed result exported and hashed")
        result["worker_termination_confirmed"] = closed.get("absence_confirmed") is True
        status_accepted = result["job_status"] in OPERATION_SUCCESS_STATUSES.get(job["operation_id"], set())
        terminal = "completed" if run["exit_code"] == 0 and status_accepted and result["worker_termination_confirmed"] else "failed"
        # Store only explicitly exported aggregate output in the review repo.
        public_dir = ROOT / "audit/evidence/cloud-runs" / job["job_id"] / attempt
        save(public_dir / "result.json", driver_result)
        result["review_result"] = ref(public_dir / "result.json")
    except Exception as exc:
        # Provider/error strings can contain credentials or task output. Keep
        # only the exception class and durable provider state for reconciliation.
        terminal = "needs_reconciliation"
        result["error_class"] = type(exc).__name__
        if worker is not None:
            if result["exports_verified"] is not True:
                try:
                    destination = state_dir / "exports" / job["job_id"] / attempt
                    partial = worker.download(job["job_id"], job["exports"], destination,
                        max_bytes=job["max_export_bytes"], allow_incomplete=True)
                    result["partial_export"] = partial
                    result["partial_evidence_scope"] = "Interrupted job checkpoint, not a completed result"
                except Exception as recovery:
                    result["checkpoint_error_class"] = type(recovery).__name__
            try:
                closed = worker.close("Stop after an incomplete queue attempt; preserve compact local evidence", allow_uncertain_job=True)
                result["worker_termination_confirmed"] = closed.get("absence_confirmed") is True
            except Exception as cleanup:
                result["cleanup_error_class"] = type(cleanup).__name__
        elif manager is not None and token is not None:
            try:
                closed = manager.close_reservation(token, "Cleanup a known owned creation after failed verification")
                result["worker_termination_confirmed"] = closed.get("absence_confirmed") is True
            except Exception as cleanup:
                result["cleanup_error_class"] = type(cleanup).__name__
    if attempt is not None:
        store.finish(job["job_id"], attempt, terminal, result)
        save(state_dir / "attempts" / f"{attempt}.json", result)
    return {"job_id": job["job_id"], "attempt_id": attempt, "state": terminal,
            "worker_termination_confirmed": result["worker_termination_confirmed"],
            "certified_tasks": 0}


def dispatch_jobs(jobs, execute, *, max_jobs, concurrency, emit, stop_admissions=lambda: None):
    """Bound local transport threads; drain running jobs after a dispatch stop.

    Capacity remains enforced by the durable provider inventory. Unknown outcomes
    stop further dispatch, while already-running jobs still export and clean up.
    """
    if type(concurrency) is not int or not 1 <= concurrency <= 50:
        raise ValueError("Concurrency must be between 1 and 50")
    pending = iter(jobs)
    dispatched = 0
    stop = False
    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        active = {}
        try:
            while active or not stop:
                while not stop and len(active) < concurrency and dispatched < max_jobs:
                    job = next(pending, None)
                    if job is None:
                        stop = True
                        break
                    active[pool.submit(execute, job)] = job["job_id"]
                    dispatched += 1
                if not active:
                    break
                finished, _ = wait(active, return_when=FIRST_COMPLETED)
                for future in finished:
                    job_id = active.pop(future)
                    try:
                        outcome = future.result()
                    except Exception as exc:
                        outcome = {"job_id": job_id, "state": "coordinator_error", "error_class": type(exc).__name__}
                    if outcome["state"] in {"needs_reconciliation", "coordinator_error", "deferred_capacity", "deferred_claim_or_budget"}:
                        stop = True
                        stop_admissions()
                    emit(outcome)
                if dispatched >= max_jobs:
                    stop = True
        except BaseException:
            stop_admissions()
            raise
    return dispatched


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "status", "run"))
    parser.add_argument("--state-dir", type=Path, default=ROOT.parent / "work/cloud-queue")
    parser.add_argument("--max-jobs", type=int, default=1)
    parser.add_argument("--concurrency", type=int, default=1)
    args = parser.parse_args()
    if args.action == "prepare":
        print(json.dumps(prepare()))
        return
    policy = read_policy()
    store = QueueStore(args.state_dir / "queue.sqlite3", ceiling_usd=policy["compute_ceiling_usd"])
    if args.action == "status":
        print(json.dumps(store.snapshot(), indent=2))
        return
    if not 1 <= args.max_jobs <= 51:
        parser.error("max-jobs must be between1 and51")
    if not 1 <= args.concurrency <= policy["max_workers"]:
        parser.error("concurrency exceeds the current shared cloud policy")
    if args.state_dir.resolve() != (ROOT.parent / "work/cloud-queue").resolve():
        parser.error("Live runs must share this audit's existing state directory and budget ledger")
    # These threads wait on cloud I/O. Avoid reserving a default multi-MiB stack
    # per thread when the user enables a large remote fleet.
    threading.stack_size(512 * 1024)
    plan = read(PLAN)
    jobs = []
    for item in plan["jobs"]:
        job = load_job_reference(item)
        store.register(job)
        states = {row["job_id"]: row["state"] for row in store.snapshot()["jobs"]}
        if states[job["job_id"]] != "pending":
            continue
        jobs.append(job)
    dispatch_jobs(jobs, lambda job: execute_one(job, store, args.state_dir),
        max_jobs=args.max_jobs, concurrency=args.concurrency,
        emit=lambda outcome: print(json.dumps(outcome), flush=True), stop_admissions=STAGING_BUDGET.stop)
    print(json.dumps(store.snapshot()), flush=True)


if __name__ == "__main__":
    main()
