#!/usr/bin/env python3
"""Prepare local Equivalence overlays and a blocked native integration recipe.

This source-only utility never imports acquired code or calls a native runner,
provider, credential service, ownership registry, queue, compiler or grader.
Private output belongs to this worktree's ignored audit/evidence directory.
"""

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import resource
import signal
import stat


TASK = "equivalence_class_divide_and_conquer"
GROUPS = ("T1_P5047", "T2_P6778", "T3_P8204", "T4_L3651", "T5_T177", "T6_P5399")
WEIGHTS = (5, 5, 10, 15, 25, 40)
EVAL_ARGV = ["python3", "/opt/p2_judge/prob/P2/eval.py", "--source-root",
             "/home/workspace/p2", "--time-factor", "1", "--time-grace", "0", "--score-sum"]
EVAL_COMMAND = "cd /home/workspace/p2 && " + " ".join(EVAL_ARGV)
EVIDENCE = "audit/evidence/"
FULL = EVIDENCE + "equivalence-six-native-integration-sol-v2/"
FIRST = EVIDENCE + "equivalence-six-native-integration-sol-v1/"
META = EVIDENCE + "equivalence-six-installed-metadata-census-sol-v2/"
READ_CAP = 1048576
TOTAL_READ_CAP = 16777216
READ_COUNT_CAP = 32
PENDING_IMAGE = "PENDING_REVIEWED_EQUIVALENCE_T3_JUDGE_IMAGE"


def bound_local_reader():
    for key, requested in ((resource.RLIMIT_AS, 134217728), (resource.RLIMIT_CPU, 5)):
        _, hard = resource.getrlimit(key)
        value = requested if hard == resource.RLIM_INFINITY else min(requested, hard)
        resource.setrlimit(key, (value, value))
    os.sched_setaffinity(0, {min(os.sched_getaffinity(0))})
    signal.alarm(18)
    os.umask(0o077)


class Reader:
    def __init__(self, root):
        self.root = root
        self.bytes = 0
        self.files = 0

    def raw(self, relative):
        path = self.root / relative
        if Path(relative).is_absolute() or ".." in Path(relative).parts:
            raise ValueError("source_reference_boundary")
        before = path.lstat()
        if not stat.S_ISREG(before.st_mode) or not 0 <= before.st_size <= READ_CAP:
            raise ValueError("source_read_cap_or_type")
        if self.files + 1 > READ_COUNT_CAP or self.bytes + before.st_size > TOTAL_READ_CAP:
            raise ValueError("aggregate_source_read_cap")
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
        with os.fdopen(fd, "rb") as handle:
            opened = os.fstat(handle.fileno())
            body = handle.read(READ_CAP + 1)
            after = os.fstat(handle.fileno())
        signature = lambda info: (info.st_dev, info.st_ino, info.st_size,
                                  info.st_mtime_ns, info.st_ctime_ns)
        if (len(body) != before.st_size or signature(before) != signature(opened)
                or signature(opened) != signature(after)):
            raise ValueError("source_unstable_or_overcap")
        self.files += 1
        self.bytes += len(body)
        return body

    def json(self, relative):
        return json.loads(self.raw(relative))


def encode(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()


def write_new(root, relative, body):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as handle:
        handle.write(body)
    return {"path": relative, "bytes": len(body), "sha256": hashlib.sha256(body).hexdigest()}


def prepare(canonical, output):
    reader = Reader(canonical)
    manifest = reader.json("tasks/" + TASK + ".json")
    if (manifest["judge"]["eval_cmd"] != EVAL_COMMAND
            or manifest["judge"]["eval_timeout"] != 900
            or manifest["cwd"] != "/home/workspace/p2"
            or manifest["submit_paths"] != ["T%d.cpp" % n for n in range(1, 7)]):
        raise ValueError("original_native_manifest_mismatch")
    dependencies = reader.json(FIRST + "dependencies.json")
    full_job = reader.json(FULL + "job.json")
    meta_job = reader.json(META + "packet/job.json")
    controls = reader.json(FIRST + "controls.json")
    meta_source = reader.json(EVIDENCE + "equivalence-six-installed-metadata-census-sol-v2-root-review/root-source-review.json")
    if meta_source["operational_admission"] is not False or full_job["automatic_retries"] != 0:
        raise ValueError("frozen_recipe_boundary_mismatch")
    inputs = {row["target"]: row for row in full_job["inputs"]}
    output.mkdir(parents=True, exist_ok=False)
    artifacts = []
    for source, destination in (
            ("t3-checker-candidate.cpp", "judge-overlay/opt/p2_judge/prob/P2/T3_P8204/data/checker.cpp"),
            ("t2-candidate.cpp", "reference-control/T2.cpp")):
        ref = inputs[source]
        body = reader.raw(ref["path"])
        if len(body) != ref["bytes"] or hashlib.sha256(body).hexdigest() != ref["sha256"]:
            raise ValueError("accepted_overlay_copy_identity")
        artifacts.append(write_new(output, destination, body))
    candidate = copy.deepcopy(manifest)
    candidate["judge"]["image_tag"] = PENDING_IMAGE
    artifacts.append(write_new(output, "native-task-template.json", encode(candidate)))
    dockerfile = ("FROM " + controls["image"]["reference"] + "\n"
                  "COPY --chown=0:0 judge-overlay/opt/p2_judge/prob/P2/T3_P8204/data/checker.cpp "
                  "/opt/p2_judge/prob/P2/T3_P8204/data/checker.cpp\n")
    artifacts.append(write_new(output, "Dockerfile.template", dockerfile.encode()))
    reference_sources = []
    for number in range(1, 7):
        target = "std%d.cpp" % number
        reference_sources.append({"component": "T%d" % number,
                                  "original": inputs[target],
                                  "candidate": inputs["t2-candidate.cpp"] if number == 2 else inputs[target],
                                  "native_submission_path": "/home/workspace/p2/T%d.cpp" % number})
    recipe = {
        "schema": "equivalence-integrated-source-recipe-v1",
        "task_id": TASK, "status": "SOURCE_ONLY_BLOCKED_ACTUAL_CENSUS_AND_ROOT_ADMISSION",
        "runnable": False, "operational_admission": False, "automatic_retries": 0,
        "native_task": {"original_manifest": dependencies["original_task_manifest"],
                        "eval_command": EVAL_COMMAND, "argv": EVAL_ARGV, "cwd": manifest["cwd"],
                        "eval_timeout_seconds": 900, "parser": "score_sum",
                        "manifest_template_only_change": "judge.image_tag",
                        "derived_judge_image": None, "derived_work_image": None},
        "roles": {"T3": "Judge checker correction; requires derived image and native manifest binding.",
                  "T2": "Finite repaired reference-control submission, not an active evaluator correction.",
                  "other_references": "Byte-identical accepted references; no claim that they pass all installed cases."},
        "reference_control_sources": reference_sources,
        "private_input_contract": {
            "suite_dir": "/opt/p2_judge/prob/P2", "groups": list(GROUPS),
            "discovery": "All directories matching T[1-6]_ must total exactly six.",
            "inputs": "Each group's data/*.in; natural numeric ordering by stem; no --case filter.",
            "answer_choice": "Same stem .out if it exists, otherwise .ans; missing answer stops.",
            "runtime": "Input file is program stdin; unchanged checker gets input/output/answer argv or token comparison.",
            "limits": "Parsed from each task statement; time factor 1, grace 0; default memory grace 16MB and checker timeout 30s.",
            "source_precedence_gate": "Prove that no higher-priority per-family std.cpp/main.cpp/name.cpp shadows mounted T1.cpp..T6.cpp.",
            "privacy": "No hidden names, raw inputs, answers, case messages or compiler stderr in public receipts.",
            "mathematical_input_validity": "Still requires task-specific corpus/specification review; this is the grader I/O contract."},
        "score_contract": {"weights": list(WEIGHTS),
                           "family_credit": "Full weight only if every case passes; otherwise half-weight times passed/total.",
                           "reuse": "Existing full-six score_oracle and accepted finite checks; weighted CASE units are not independent cases.",
                           "required": "All six complete summaries plus matching CASE/TOTAL_SCORE/CASES_OK/CASES_TOTAL joins; zero exit alone is insufficient."},
        "metadata_first": {"existing_job": meta_job["job_id"], "job_path": META + "packet/job.json",
                           "source_review_path": EVIDENCE + "equivalence-six-installed-metadata-census-sol-v2-root-review/root-source-review.json",
                           "actual_accepted_result": None,
                           "required": "Six complete stable ordinary-ancestor rows; nonempty .in groups, selected regular answers, no missing answers; threshold prediction joined to resource envelope.",
                           "historical_stop": "reserve OutcomeUnknown before attempt/worker; no native failure or permission cause established.",
                           "retry": "Root reconciles canonical ownership/reservation state and independently admits any next use; this recipe does not retry."},
        "execution_reuse": {"fullsix_job": full_job["job_id"], "job_path": FULL + "job.json",
                            "scientific_inputs": full_job["inputs"],
                            "maintained_runtime_refs": dependencies["unchanged_maintained_runtime_refs"],
                            "root_selects_current_runner_grant_and_accounting": True,
                            "controller_created": False},
        "resources": {"frozen_fullsix_limits": full_job["science"]["task_native_limits"],
                      "frozen_metadata_limits": meta_job["science"]["task_native_limits"],
                      "existing_stage_bytes": sum(row["bytes"] for row in full_job["inputs"]),
                      "max_export_bytes": full_job["max_export_bytes"],
                      "important_limit": "Existing full-six caller cap150s/native180s is shorter than the declared900s. Incomplete output is a capped audit observation, not a task failure.",
                      "after_census": "Reuse limits if adequate; otherwise root reviews a measured finite streaming/resource/time/cost extension before any launch. No cap change is authorized here.",
                      "cost": "No new worker is selected or reserved; root reprices the selected frozen job under current policy before its operational grant."},
        "required_next_checks": [
            "Different source review of this frozen local materialization, roles and native template.",
            "Root-only ownership reconciliation and actual frozen metadata census admission; no blind rerun.",
            "Different/root result review of census; a collection receipt is not data readiness.",
            "Resolve source precedence, six discovery names, body-stream and native resource fit without repeating accepted corpus hashes.",
            "Root admission of two matched sequential original/candidate full-six callers using maintained runner.",
            "Retain started/terminal/timeout/compile/parser facts separately, even if a later parser or settlement fails.",
            "Join paired complete summaries and score markers; independently review regressions and unchanged-score counterevidence.",
            "Build/freeze/review the one-file derived judge image and bind its actual identity in native task format before treating it as an integrated release candidate."],
        "accepted_evidence_reused": dependencies["accepted_evidence_refs"],
        "limits": ["No fresh T3 negative included; accepted finite at/above-limit evidence reused.",
                   "T2 singleton mechanism/corpus incidence, full-suite behavior, provenance/rights/domain/repeatability remain pending.",
                   "No task disposition, five-gate field, image execution flag, certification or benchmark-publication change."],
        "actions": {"native": 0, "provider": 0, "credential": 0, "model": 0,
                    "shared_queue_registry_ledger_mutation": 0, "corpus_body_reads_or_hashes": 0},
        "preparation_reads": {"files": reader.files, "bytes": reader.bytes,
                              "per_file_cap": READ_CAP, "total_cap": TOTAL_READ_CAP,
                              "file_count_cap": READ_COUNT_CAP},
        "artifacts": artifacts,
    }
    artifacts.append(write_new(output, "recipe.json", encode(recipe)))
    return {"status": recipe["status"], "operational_admission": False,
            "artifact_count": len(artifacts), "native_provider_model_calls": 0,
            "preparation_read_files": reader.files, "preparation_read_bytes": reader.bytes}


def main():
    bound_local_reader()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--canonical-root", type=Path, required=True)
    args = parser.parse_args()
    worktree = Path(__file__).resolve().parents[2]
    output = worktree / "audit/evidence/equivalence-integrated-sol-v1/prepared"
    canonical = args.canonical_root.resolve(strict=True)
    if canonical == worktree:
        raise ValueError("canonical_root_must_be_separate")
    print(json.dumps(prepare(canonical, output), sort_keys=True))


if __name__ == "__main__":
    main()
