"""Adversarial integrity tests using explicitly synthetic evidence, not real tasks."""
import copy
import hashlib
import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path


SPEC = importlib.util.spec_from_file_location("check_release", Path(__file__).resolve().parents[1] / "tools/check_release.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def write(root, path, value):
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    return {"path": path, "sha256": hashlib.sha256(target.read_bytes()).hexdigest()}


def read(root, path):
    return json.loads((root / path).read_text(encoding="utf-8"))


def fixture(root):
    """51 synthetic dispositions: one retained and 50 reasoned exclusions.

    This tests completeness without claiming these synthetic prose logs prove
    real science. The validator explicitly cannot establish that on its own.
    """
    ids = ["fixture_{:02}".format(n) for n in range(51)]
    raw = write(root, "evidence/synthetic-log.json", {"notice": "SYNTHETIC TEST FIXTURE ONLY"})
    harness_file = write(root, "sforge/synthetic.json", {"notice": "SYNTHETIC HARNESS"})
    dependency = root / "pyproject.toml"
    dependency.write_text('[project]\nname = "synthetic-fixture"\nversion = "1.0.0"\ndependencies = ["synthetic==1.0"]\n')
    dependency_ref = {"path": "pyproject.toml", "sha256": MODULE.digest(dependency)}
    environment = write(root, "evidence/runtime.json", {"status": "pinned", "python_version": "3.12.0", "platform": "linux/amd64", "packages": [{"name": "synthetic", "version": "1.0"}], "evidence": [raw]})
    harness_inventory = write(root, "evidence/harness.json", {"files": [harness_file, dependency_ref], "runtime_environment": environment})
    claim_catalog = write(root, "audit/claim-applicability.json", {"claims": []})
    hashes = {}
    for index, task_id in enumerate(ids):
        path = "tasks/{}.json".format(task_id)
        manifest = {"task_id": task_id, "platform": "linux/amd64", "work": {"image_tag": "aabbccddee11"}, "judge": {"image_tag": "bbccddee1122"}}
        manifest_sha = write(root, path, manifest)["sha256"]
        hashes[path] = manifest_sha
        decision = "retain" if index == 0 else "exclude"
        record = {"schema_version": 1, "task_id": task_id,
                  "source": {"manifest_path": path, "manifest_sha256": manifest_sha, "dataset_revision": "fixture-dataset", "source_revision": "fixture-code"},
                  "candidate": {"manifest_path": path, "manifest_sha256": manifest_sha, "changes": []},
                  "disposition": {"decision": decision, "status": "reviewed", "rationale": "Synthetic disposition for gate tests.", "reviews": [], "exclusion_evidence": [raw]},
                  "claims": [], "artifacts": {}, "gates": {}}
        for number in range(3):
            review = {"task_id": task_id, "manifest_sha256": manifest_sha, "decision": decision,
                      "result": "approved", "reviewer": "reviewer-{}".format(number), "method": "method-{}".format(number),
                      "limitations": "Synthetic fixture has no scientific claim.", "rationale": "Controlled integrity test.", "evidence": [raw]}
            record["disposition"]["reviews"].append(write(root, "evidence/{}/review-{}.json".format(task_id, number), review))
        if index == 0:
            for name in MODULE.ARTIFACTS:
                if name.endswith("_image"):
                    config_ref = write(root, "evidence/{}/{}-config.json".format(task_id, name), {"os": "linux", "architecture": "amd64"})
                    artifact = {"schemaVersion": 2, "config": {"digest": "sha256:" + config_ref["sha256"]}, "layers": [{"digest": "sha256:" + "b" * 64}]}
                    kind = "oci_manifest"
                else:
                    artifact = {"task_id": task_id, "role": name, "files": [raw]}
                    kind = "file_inventory"
                ref = write(root, "evidence/{}/{}.json".format(task_id, name), artifact)
                record["artifacts"][name] = {"kind": kind, "status": "pinned", "sha256": ref["sha256"], "record": ref}
                if name.endswith("_image"):
                    role = name.split("_")[0]
                    record["artifacts"][name].update({"source_reference": manifest[role]["image_tag"], "platform": "linux/amd64", "config": config_ref})
            artifacts = {name: record["artifacts"][name]["sha256"] for name in MODULE.ARTIFACTS}
            for name, requirements in MODULE.REQUIREMENTS.items():
                report = {"task_id": task_id, "gate": name, "manifest_sha256": manifest_sha, "artifact_sha256": artifacts,
                          "harness_sha256": harness_inventory["sha256"], "result": "passed", "reviewer": name + "-reviewer", "method": name + "-method",
                          "limitations": "Synthetic fixture; tests structure only.",
                          "assertions": {requirement: {"result": "passed", "finding": "Synthetic assertion.", "evidence": [raw]} for requirement in requirements}}
                record["gates"][name] = {"status": "passed", "report": write(root, "evidence/{}/{}.json".format(task_id, name + "-gate"), report)}
        bundle_sha = MODULE.review_bundle_hash(record, harness_inventory["sha256"], claim_catalog["sha256"])
        reviews = []
        for ref in record["disposition"]["reviews"]:
            report = read(root, ref["path"])
            report["review_bundle_sha256"] = bundle_sha
            reviews.append(write(root, ref["path"], report))
        record["disposition"]["reviews"] = reviews
        write(root, "audit/tasks/{}.json".format(task_id), record)
    lock = {"upstream_sha256": hashes, "dataset_revision": "fixture-dataset", "source_revision": "fixture-code"}
    lock_ref = write(root, "audit/upstream-lock.json", lock)
    registry = {"schema_version": 1, "scope": copy.deepcopy(MODULE.SCOPE), "upstream_lock_sha256": lock_ref["sha256"],
                "task_ids": ids, "claim_catalog": claim_catalog, "release": {"status": "candidate", "included_task_ids": ids[:1], "excluded_task_ids": ids[1:], "harness_inventory": harness_inventory}}
    write(root, "audit/task-registry.json", registry)


class ReleaseGatesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.template_dir = tempfile.TemporaryDirectory()
        cls.template = Path(cls.template_dir.name)
        fixture(cls.template)

    @classmethod
    def tearDownClass(cls):
        cls.template_dir.cleanup()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        shutil.copytree(self.template, self.root, dirs_exist_ok=True)
        self.path = "audit/tasks/fixture_00.json"
        self.task = read(self.root, self.path)

    def tearDown(self):
        self.temp.cleanup()

    def blocked(self, fragment):
        result = MODULE.check_release(self.root)
        self.assertFalse(result["ready"])
        self.assertTrue(any(fragment in error for error in result["errors"]), result["errors"])

    def save_task(self):
        write(self.root, self.path, self.task)

    def mutate_gate(self, name, change):
        ref = self.task["gates"][name]["report"]
        report = read(self.root, ref["path"])
        change(report)
        self.task["gates"][name]["report"] = write(self.root, ref["path"], report)
        self.save_task()

    def test_complete_synthetic_public_scope_passes_integrity_only(self):
        result = MODULE.check_release(self.root)
        self.assertTrue(result["ready"], result["errors"])
        self.assertEqual(result["counts"], {"public": 51, "included": 1, "excluded": 50, "pending": 0})
        self.assertIn("scientific correctness", result["meaning"])

    def test_pending_disposition_is_not_a_default_retention(self):
        self.task["disposition"].update(decision="review", status="pending")
        self.save_task()
        self.blocked("disposition is pending")

    def test_silently_dropping_public_task_fails_even_with_rewritten_lock(self):
        tid = "fixture_50"
        (self.root / "audit/tasks" / (tid + ".json")).unlink()
        (self.root / "tasks" / (tid + ".json")).unlink()
        lock = read(self.root, "audit/upstream-lock.json")
        del lock["upstream_sha256"]["tasks/" + tid + ".json"]
        ref = write(self.root, "audit/upstream-lock.json", lock)
        registry = read(self.root, "audit/task-registry.json")
        registry["task_ids"].remove(tid)
        registry["release"]["excluded_task_ids"].remove(tid)
        registry["upstream_lock_sha256"] = ref["sha256"]
        write(self.root, "audit/task-registry.json", registry)
        self.blocked("preserve all 51")

    def test_no_134_task_certification_claim(self):
        registry = read(self.root, "audit/task-registry.json")
        registry["scope"]["certification_scope"] = "all_134_tasks"
        write(self.root, "audit/task-registry.json", registry)
        self.blocked("no 134-task certification")

    def test_excluded_task_requires_reason_and_evidence(self):
        path = "audit/tasks/fixture_01.json"
        task = read(self.root, path)
        task["disposition"]["rationale"] = ""
        task["disposition"]["exclusion_evidence"] = []
        write(self.root, path, task)
        self.blocked("disposition rationale required")
        self.blocked("at least one evidence reference required")

    def test_task_edit_invalidates_prior_review(self):
        path = "tasks/fixture_00.json"
        manifest = read(self.root, path)
        manifest["judge"]["eval_cmd"] = "changed"
        write(self.root, path, manifest)
        self.blocked("candidate manifest changed since review")
        self.blocked("review is not bound to this task")

    def test_fresh_hash_cannot_hide_undocumented_repair(self):
        path = "tasks/fixture_00.json"
        manifest = read(self.root, path)
        manifest["judge"]["eval_cmd"] = "changed"
        self.task["candidate"]["manifest_sha256"] = write(self.root, path, manifest)["sha256"]
        self.task["disposition"]["decision"] = "repair"
        self.save_task()
        self.blocked("repairs require explicit changes")

    def test_tampered_evidence_bytes_fail(self):
        (self.root / "evidence/synthetic-log.json").write_text("modified")
        self.blocked("evidence SHA256 mismatch")

    def test_gate_report_bound_to_all_artifacts(self):
        self.mutate_gate("verifier", lambda r: r["artifact_sha256"].update(data="c" * 64))
        self.blocked("report artifact identities do not match")

    def test_pass_label_without_assertions_fails(self):
        self.mutate_gate("verifier", lambda r: r.update(assertions={}))
        self.blocked("positive_controls has no passing substantiated finding")

    def test_unresolved_image_tag_is_not_immutable_identity(self):
        self.task["artifacts"]["judge_image"]["status"] = "unresolved"
        self.save_task()
        self.blocked("artifact has not been acquired and pinned")

    def test_wrong_image_tag_does_not_verify_current_config(self):
        self.task["artifacts"]["work_image"]["source_reference"] = "wrong-tag"
        self.save_task()
        self.blocked("artifact tag differs from current task configuration")

    def test_wrong_image_config_is_not_a_pinned_executable_image(self):
        ref = write(self.root, "evidence/wrong-config.json", {"os": "linux", "architecture": "arm64"})
        self.task["artifacts"]["work_image"]["config"] = ref
        self.save_task()
        self.blocked("config content identity differs from image descriptor")
        self.blocked("acquired config platform differs from task")

    def test_same_reviewer_is_not_independent_reproduction(self):
        self.mutate_gate("independent_reproduction", lambda r: r.update(reviewer="execution-reviewer"))
        self.blocked("different reviewer and method")

    def test_three_copies_of_one_review_do_not_count_as_three_reviews(self):
        ref = self.task["disposition"]["reviews"][0]
        self.task["disposition"]["reviews"] = [ref, ref, ref]
        self.save_task()
        self.blocked("three distinct reviewer identities and methods")

    def test_evidence_outside_repository_rejected(self):
        ref = self.task["gates"]["data"]["report"]
        ref["path"] = "../outside.json"
        self.save_task()
        self.blocked("path escapes repository")

    def test_release_cannot_hide_an_included_task(self):
        registry = read(self.root, "audit/task-registry.json")
        registry["release"]["included_task_ids"] = []
        write(self.root, "audit/task-registry.json", registry)
        self.blocked("release inclusion/exclusion must exactly match")

    def test_unknown_task_is_not_silently_ignored(self):
        write(self.root, "audit/tasks/unregistered.json", {})
        self.blocked("file IDs differ from public task scope")

    def test_missing_claim_reference_fails(self):
        self.task["claims"] = [{"claim_id": "NONEXISTENT", "path": "audit/claims/NONEXISTENT.json", "sha256": "a" * 64}]
        self.save_task()
        self.blocked("missing file audit/claims/NONEXISTENT.json")

    def test_known_claim_cannot_be_ignored_on_retained_task(self):
        ref = write(self.root, "audit/claims/fixture.json", {"claim_id": "FIXTURE"})
        ref.update(claim_id="FIXTURE", impact={"status": "pending", "rationale": "", "evidence": []})
        self.task["claims"] = [ref]
        self.save_task()
        self.blocked("claim task impact remains unresolved")

    def test_harness_edits_invalidate_prior_evidence(self):
        write(self.root, "sforge/synthetic.json", {"notice": "MODIFIED"})
        self.blocked("evidence SHA256 mismatch")

    def test_uninventoried_harness_file_fails(self):
        write(self.root, "sforge/unrecorded.json", {})
        self.blocked("cover every current sforge file")

    def test_gate_cannot_use_another_harness_inventory(self):
        self.mutate_gate("execution", lambda r: r.update(harness_sha256="a" * 64))
        self.blocked("report not bound to current harness inventory")

    def test_claim_file_cannot_be_omitted_from_catalog(self):
        write(self.root, "audit/claims/omitted.json", {"claim_id": "OMITTED", "scope": {"task": "fixture_00"}})
        self.blocked("must account for every claim file exactly once")

    def test_catalog_claim_cannot_be_omitted_from_task(self):
        ref = write(self.root, "audit/claims/omitted.json", {"claim_id": "OMITTED", "scope": {"task": "fixture_00"}})
        ref.update(claim_id="OMITTED", task_ids=["fixture_00"], rationale="Direct synthetic task scope.")
        catalog = write(self.root, "audit/claim-applicability.json", {"claims": [ref]})
        registry = read(self.root, "audit/task-registry.json")
        registry["claim_catalog"] = catalog
        write(self.root, "audit/task-registry.json", registry)
        self.blocked("task claim references must exactly cover the applicability catalog")

    def test_claim_stated_task_scope_cannot_be_reclassified_as_no_tasks(self):
        ref = write(self.root, "audit/claims/omitted.json", {"claim_id": "OMITTED", "scope": {"task": "fixture_00"}})
        ref.update(claim_id="OMITTED", task_ids=[], rationale="False empty applicability.")
        catalog = write(self.root, "audit/claim-applicability.json", {"claims": [ref]})
        registry = read(self.root, "audit/task-registry.json")
        registry["claim_catalog"] = catalog
        write(self.root, "audit/task-registry.json", registry)
        self.blocked("cannot omit task applicability stated in the claim")

    def test_changed_data_and_fresh_gate_reports_do_not_reuse_old_approvals(self):
        ref = self.task["artifacts"]["data"]["record"]
        inventory = read(self.root, ref["path"])
        inventory["files"].append(write(self.root, "evidence/new-data.json", {"synthetic": "NEW DATA"}))
        new_ref = write(self.root, ref["path"], inventory)
        self.task["artifacts"]["data"].update(record=new_ref, sha256=new_ref["sha256"])
        for name in MODULE.REQUIREMENTS:
            ref = self.task["gates"][name]["report"]
            report = read(self.root, ref["path"])
            report["artifact_sha256"]["data"] = new_ref["sha256"]
            self.task["gates"][name]["report"] = write(self.root, ref["path"], report)
        self.save_task()
        self.blocked("review is stale for the current artifacts")

    def test_dependency_change_invalidates_runtime_evidence(self):
        path = self.root / "pyproject.toml"
        path.write_text(path.read_text().replace("synthetic==1.0", "synthetic==99.0"))
        self.blocked("evidence SHA256 mismatch")

    def test_missing_runtime_record_blocks_release(self):
        path = "evidence/harness.json"
        inventory = read(self.root, path)
        del inventory["runtime_environment"]
        ref = write(self.root, path, inventory)
        registry = read(self.root, "audit/task-registry.json")
        registry["release"]["harness_inventory"] = ref
        write(self.root, "audit/task-registry.json", registry)
        self.blocked("missing evidence reference with SHA256")

    def test_malformed_types_fail_closed_without_traceback(self):
        self.task["artifacts"] = []
        self.save_task()
        self.blocked("malformed or unreadable input")


if __name__ == "__main__":
    unittest.main()
