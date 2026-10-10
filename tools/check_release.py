#!/usr/bin/env python3
"""Fail-closed evidence-integrity gate; passing is necessary, not certification.

The v1 schema and limits are documented in audit/reviews/task_registry.txt;
the opt-in v2 contract is in audit/schemas/content_inventory_v2.txt.
Only standard-library modules are used; no benchmark task code is executed.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path


PUBLIC_TASKS = 51
ADVERTISED_TASKS = 134
UNRELEASED_TASKS = 83
ARTIFACTS = ("work_image", "judge_image", "verifier", "data")
REQUIREMENTS = {
    "specification": ("requirements_complete", "scoring_matches_specification", "submission_contract", "feedback_split_policy"),
    "verifier": ("positive_controls", "negative_controls", "boundary_controls", "mutation_tests", "independent_oracle"),
    "data": ("provenance_and_license", "integrity", "split_overlap", "label_quality", "case_diversity"),
    "execution": ("clean_environment", "baseline_reproduced", "resource_contract", "failure_paths", "repeatability"),
    "independent_reproduction": ("fresh_execution", "independent_method", "result_comparison", "fresh_cases_or_justified_fixed_suite"),
}
SHA256 = re.compile(r"^[0-9a-f]{64}$")
SCOPE = {
    "public_task_count": PUBLIC_TASKS,
    "advertised_task_count": ADVERTISED_TASKS,
    "unreleased_task_count": UNRELEASED_TASKS,
    "unreleased_disposition": "out_of_scope_unavailable",
    "certification_scope": "public_tasks_only",
}


def digest(path):
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key: " + key)
        result[key] = value
    return result


def reject_constant(value):
    raise ValueError("non-finite JSON number: " + value)


def same_json(left, right):
    """Do not let Python's True == 1 == 1.0 weaken typed receipt bindings."""
    return json.dumps(left, sort_keys=True, separators=(",", ":"), allow_nan=False) == json.dumps(
        right, sort_keys=True, separators=(",", ":"), allow_nan=False)


def review_bundle_hash(record, harness_sha256, claim_catalog_sha256):
    """Hash the material decision inputs; exclude approvals to avoid recursion."""
    disposition = record.get("disposition", {})
    bundle = {"task_id": record.get("task_id"), "candidate": record.get("candidate"),
              "harness_sha256": harness_sha256, "claim_catalog_sha256": claim_catalog_sha256,
              "disposition": {key: disposition.get(key) for key in ("decision", "status", "rationale", "exclusion_evidence")},
              "claims": record.get("claims"), "artifacts": record.get("artifacts"), "gates": record.get("gates")}
    return hashlib.sha256(json.dumps(bundle, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()


class ReleaseCheck:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.errors = []
        self.counts = {"public": 0, "included": 0, "excluded": 0, "pending": 0}
        self.harness_sha256 = None
        self.claim_catalog_sha256 = None
        self.claims_by_task = {}

    def error(self, where, message):
        self.errors.append("{}: {}".format(where, message))

    def local(self, name, where):
        if not isinstance(name, str) or not name or Path(name).is_absolute():
            self.error(where, "expected repository-relative file path")
            return None
        path = (self.root / name).resolve()
        try:
            path.relative_to(self.root)
        except ValueError:
            self.error(where, "path escapes repository")
            return None
        if not path.is_file():
            self.error(where, "missing file {}".format(name))
            return None
        return path

    def read(self, name, where):
        path = self.local(name, where)
        if path is None:
            return None
        try:
            value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_object,
                               parse_constant=reject_constant)
        except (ValueError, UnicodeError, OSError) as exc:
            self.error(where, "invalid JSON: {}".format(exc))
            return None
        if not isinstance(value, dict):
            self.error(where, "expected JSON object")
            return None
        return value

    def reference(self, ref, where, as_json=False):
        if not isinstance(ref, dict) or not SHA256.fullmatch(str(ref.get("sha256", ""))):
            self.error(where, "missing evidence reference with SHA256")
            return None
        path = self.local(ref.get("path"), where)
        if path is None:
            return None
        if digest(path) != ref["sha256"]:
            self.error(where, "evidence SHA256 mismatch")
            return None
        return self.read(ref["path"], where) if as_json else path

    def references(self, refs, where):
        if not isinstance(refs, list) or not refs:
            self.error(where, "at least one evidence reference required")
            return
        for ref in refs:
            self.reference(ref, where)

    def reviews(self, reviews, task_id, manifest_sha, decision, bundle_sha):
        where = task_id + "/disposition"
        if not isinstance(reviews, list) or len(reviews) < 3:
            self.error(where, "three independent review records required")
            return
        identities = set()
        methods = set()
        for ref in reviews:
            report = self.reference(ref, where, as_json=True)
            if report is None:
                continue
            reviewer = report.get("reviewer")
            method = report.get("method")
            if not isinstance(reviewer, str) or not reviewer.strip():
                self.error(where, "reviewer identity required")
            else:
                identities.add(reviewer.strip())
            if not isinstance(method, str) or not method.strip():
                self.error(where, "independent review method required")
            else:
                methods.add(method.strip())
            if report.get("task_id") != task_id or report.get("manifest_sha256") != manifest_sha:
                self.error(where, "review is not bound to this task and current manifest")
            if report.get("review_bundle_sha256") != bundle_sha:
                self.error(where, "review is stale for the current artifacts, harness, gates or claim-impact decisions")
            if report.get("decision") != decision or report.get("result") != "approved":
                self.error(where, "review did not approve this disposition")
            if not report.get("limitations") or not report.get("rationale"):
                self.error(where, "review rationale and explicit limitations required")
            self.references(report.get("evidence"), where + "/review")
        if len(identities) < 3 or len(methods) < 3:
            self.error(where, "three distinct reviewer identities and methods required")

    def harness(self, ref):
        inventory = self.reference(ref, "release/harness", as_json=True)
        if inventory is None:
            return
        self.harness_sha256 = ref["sha256"]
        files = inventory.get("files")
        self.references(files, "release/harness/files")
        if not isinstance(files, list):
            return
        expected = sorted(str(p.relative_to(self.root)) for p in (self.root / "sforge").rglob("*")
                          if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc")
        dependencies = set()
        for pattern in ("pyproject.toml", "uv.lock", "poetry.lock", "pdm.lock", "Pipfile", "Pipfile.lock", "requirements*.txt", "environment*.yml", "environment*.yaml"):
            dependencies.update(str(p.relative_to(self.root)) for p in self.root.glob(pattern) if p.is_file())
        if "pyproject.toml" not in dependencies:
            self.error("release/harness", "pyproject.toml dependency definition required")
        expected = sorted(expected + list(dependencies))
        observed = sorted(item.get("path", "") for item in files if isinstance(item, dict))
        if not expected or observed != expected:
            self.error("release/harness", "inventory must cover every current sforge file and dependency definition exactly once")
        environment = self.reference(inventory.get("runtime_environment"), "release/harness/runtime_environment", as_json=True)
        if environment is not None:
            if environment.get("status") != "pinned" or not environment.get("python_version") or not environment.get("platform"):
                self.error("release/harness/runtime_environment", "resolved runtime identity required")
            packages = environment.get("packages")
            if not isinstance(packages, list) or not packages or any(not isinstance(p, dict) or not p.get("name") or not p.get("version") for p in packages):
                self.error("release/harness/runtime_environment", "resolved package versions required")
            self.references(environment.get("evidence"), "release/harness/runtime_environment/evidence")

    def claim_catalog(self, ref, task_ids):
        catalog = self.reference(ref, "claim-catalog", as_json=True)
        self.claims_by_task = {task_id: {} for task_id in task_ids}
        if catalog is None:
            return
        self.claim_catalog_sha256 = ref["sha256"]
        entries = catalog.get("claims")
        if not isinstance(entries, list):
            self.error("claim-catalog", "explicit claims array required")
            return
        recorded_paths, recorded_ids = [], []
        for entry in entries:
            claim = self.reference(entry, "claim-catalog/claim", as_json=True)
            if claim is None:
                continue
            recorded_paths.append(entry["path"])
            claim_id = claim.get("claim_id")
            recorded_ids.append(claim_id)
            if not claim_id or entry.get("claim_id") != claim_id:
                self.error("claim-catalog", "claim identity mismatch")
            ids = entry.get("task_ids")
            if not isinstance(ids, list) or ids != sorted(set(ids)) or any(i not in task_ids for i in ids):
                self.error("claim-catalog", "applicable task IDs must be sorted, unique and in public scope")
                continue
            scope = claim.get("scope", {})
            direct = ([scope["task"]] if scope.get("task") else []) + scope.get("real_public_manifests_using_parser", [])
            if not set(direct).issubset(ids):
                self.error("claim-catalog", "cannot omit task applicability stated in the claim")
            if not entry.get("rationale"):
                self.error("claim-catalog", "applicability rationale required, including benchmark-only claims")
            for task_id in ids:
                self.claims_by_task[task_id][claim_id] = {key: entry[key] for key in ("claim_id", "path", "sha256")}
        actual = sorted(str(p.relative_to(self.root)) for p in (self.root / "audit/claims").glob("*.json"))
        if sorted(recorded_paths) != actual or len(recorded_ids) != len(set(recorded_ids)):
            self.error("claim-catalog", "must account for every claim file exactly once with unique IDs")

    def content_fields(self, value, fields, where):
        if not isinstance(value, dict) or set(value) != set(fields.split()):
            self.error(where, "content schema requires exactly these fields: " + fields)
            return False
        return True

    def content_path(self, value, where, absolute=False):
        if (not isinstance(value, str) or not value or "\\" in value
                or any(ord(c) < 32 or 127 <= ord(c) <= 159 for c in value)
                or value.startswith("/") != absolute
                or any(part in ("", ".", "..") for part in value[int(absolute):].split("/"))
                or re.match(r"^[A-Za-z]:", value)):
            self.error(where, "normalized {}path required".format("absolute container " if absolute else "relative "))
            return False
        return True

    def content_reference(self, ref, where, as_json=False):
        """v2 references keep v1 containment and additionally reject all symlinks."""
        if not self.content_fields(ref, "path sha256", where):
            return None
        if not self.content_path(ref["path"], where):
            return None
        current = self.root
        for part in ref["path"].split("/"):
            current = current / part
            if current.is_symlink():
                self.error(where, "content references cannot traverse symlinks")
                return None
        return self.reference(ref, where, as_json=as_json)

    def content_references(self, refs, where):
        if not isinstance(refs, list) or not refs:
            self.error(where, "nonempty content reference list required")
            return
        paths = []
        for ref in refs:
            self.content_reference(ref, where)
            if isinstance(ref, dict) and isinstance(ref.get("path"), str):
                paths.append(ref["path"])
        if paths != sorted(set(paths)) or len(paths) != len(refs):
            self.error(where, "content reference paths must be sorted and unique")

    def content_size_hash(self, sha, size, where):
        if not isinstance(sha, str) or not SHA256.fullmatch(sha):
            self.error(where, "content SHA256 required")
        if type(size) is not int or size < 0:
            self.error(where, "content size must be a nonnegative integer")

    def content_report(self, ref, kind, task_id, role, manifest_sha, paths, where, extra=""):
        report = self.content_reference(ref, where, as_json=True)
        fields = "schema_version kind task_id role candidate_manifest_sha256 member_paths result reviewer method limitations evidence"
        if not self.content_fields(report, fields + (" " + extra if extra else ""), where):
            return None
        if (type(report["schema_version"]) is not int or report["schema_version"] != 1
                or report["kind"] != kind or report["task_id"] != task_id or report["role"] != role
                or report["candidate_manifest_sha256"] != manifest_sha):
            self.error(where, "content report schema/task/role/candidate binding mismatch")
        if report["member_paths"] != paths:
            self.error(where, "content report must cover the exact frozen member paths")
        if report["result"] != "reviewed":
            self.error(where, "content report must be explicitly reviewed")
        for field in ("reviewer", "method", "limitations"):
            if not isinstance(report[field], str) or not report[field].strip():
                self.error(where, "content report requires " + field)
        self.content_references(report["evidence"], where + "/evidence")
        return report

    def content_inventory(self, task_id, role, record, manifest, manifest_sha, artifacts, where):
        """Validate original-content receipts offline; never retrieve or execute them.

        v2 deliberately does not accept selected-layer, patched/overlay, or
        generated-content proofs. Those need separate versioned contracts.
        Receipt consistency is not an attestation of its author's truthfulness.
        """
        fields = "schema_version kind task_id role candidate_manifest_sha256 content_state identity_scope members coverage retrieval provenance disclosure"
        if not self.content_fields(record, fields, where):
            return
        if (type(record["schema_version"]) is not int or record["schema_version"] != 2
                or record["kind"] != "content_inventory" or role not in ("verifier", "data")
                or record["task_id"] != task_id or record["role"] != role
                or record["candidate_manifest_sha256"] != manifest_sha or not manifest_sha):
            self.error(where, "content inventory schema/task/role/candidate binding mismatch")
        if record["content_state"] != "original" or record["identity_scope"] != "effective_filesystem":
            self.error(where, "only original effective-filesystem content is supported; no generated/overlay/selected-layer proof")
        members = record["members"]
        if not isinstance(members, list) or not members:
            self.error(where, "content inventory needs nonempty members")
            return
        paths, images = [], {}
        for member in members:
            loc = where + "/members"
            if not self.content_fields(member, "logical_path content_sha256 size_bytes origin", loc):
                continue
            path = member["logical_path"]
            if self.content_path(path, loc):
                paths.append(path)
            self.content_size_hash(member["content_sha256"], member["size_bytes"], loc)
            origin = member["origin"]
            if not isinstance(origin, dict):
                self.error(loc, "typed content origin required")
                continue
            if origin.get("kind") == "repository_file":
                if not self.content_fields(origin, "kind reference", loc):
                    continue
                observed = self.content_reference(origin["reference"], loc)
                if observed is not None and (digest(observed) != member["content_sha256"] or observed.stat().st_size != member["size_bytes"]):
                    self.error(loc, "repository content hash/size differs from member")
            elif origin.get("kind") == "oci_file":
                fields = "kind source_image_role image_manifest_sha256 image_config_sha256 platform container_path file_type layer_index layer_digest archive_chain"
                if not self.content_fields(origin, fields, loc):
                    continue
                self.content_path(origin["container_path"], loc, absolute=True)
                if origin["file_type"] != "regular":
                    self.error(loc, "only regular OCI files are supported")
                image_role = origin["source_image_role"]
                if image_role not in ("work_image", "judge_image") or not isinstance(artifacts, dict):
                    self.error(loc, "OCI origin must name the task's work_image or judge_image role")
                    continue
                item = artifacts.get(image_role)
                before = len(self.errors)
                image_sha = self.artifact(task_id, image_role, item, manifest)
                if not isinstance(item, dict):
                    continue
                image = self.content_reference(item.get("record"), loc + "/image", as_json=True)
                config = self.content_reference(item.get("config"), loc + "/config", as_json=True)
                if len(self.errors) != before or image is None or config is None:
                    continue
                expected_image = {"image_manifest_sha256": image_sha,
                                  "image_config_sha256": item["config"]["sha256"],
                                  "platform": manifest.get("platform")}
                if any(origin[key] != value for key, value in expected_image.items()):
                    self.error(loc, "OCI role/manifest/config/platform identity differs from pinned task image")
                images[image_role] = expected_image
                layers = image.get("layers", [])
                index = origin["layer_index"]
                if type(index) is not int or not 0 <= index < len(layers) or layers[index].get("digest") != origin["layer_digest"]:
                    self.error(loc, "OCI outer layer ordinal/digest differs from platform manifest")
                chain = origin["archive_chain"]
                if not isinstance(chain, list):
                    self.error(loc, "ordered archive chain list required")
                else:
                    for archive in chain:
                        if self.content_fields(archive, "archive_sha256 archive_size_bytes member_path member_type", loc + "/archive"):
                            self.content_size_hash(archive["archive_sha256"], archive["archive_size_bytes"], loc)
                            self.content_path(archive["member_path"], loc)
                            if archive["member_type"] != "regular":
                                self.error(loc, "only regular archive members are supported")
            else:
                self.error(loc, "unsupported content origin kind")
        if paths != sorted(set(paths)) or len(paths) != len(members):
            self.error(where, "logical member paths must be normalized, sorted and unique")
        self.content_report(record["coverage"], "content_coverage", task_id, role, manifest_sha, paths, where + "/coverage")
        provenance = self.content_report(record["provenance"], "content_provenance", task_id, role, manifest_sha, paths,
                                         where + "/provenance", "members")
        if provenance is not None:
            entries = provenance["members"]
            if (not isinstance(entries, list) or len(entries) != len(members)
                    or any(not isinstance(e, dict) for e in entries)
                    or [e["logical_path"] if "logical_path" in e else None for e in entries] != paths):
                self.error(where, "provenance must account for each content member exactly once")
            else:
                for entry, member in zip(entries, members):
                    fields = "logical_path source revision derivation notice release_form access"
                    if not self.content_fields(entry, fields, where + "/provenance/member"):
                        continue
                    for field in ("source", "revision", "derivation", "access"):
                        if not isinstance(entry[field], str) or not entry[field].strip():
                            self.error(where, "provenance requires " + field)
                    origin = member.get("origin") if isinstance(member, dict) else None
                    if not isinstance(origin, dict):
                        self.error(where + "/provenance/member", "typed content origin required for release-form binding")
                        continue
                    expected_form = "repository_bytes" if origin.get("kind") == "repository_file" else "external_reference_only"
                    if entry["release_form"] != expected_form:
                        self.error(where, "provenance release form must distinguish local bytes from external content")
                    self.content_reference(entry["notice"], where + "/provenance/notice")
        self.content_report(record["disclosure"], "content_disclosure", task_id, role, manifest_sha, paths, where + "/disclosure")
        retrieval = record["retrieval"]
        if not self.content_fields(retrieval, "recipe driver inputs receipt job_id attempt_id", where + "/retrieval"):
            return
        for field in ("job_id", "attempt_id"):
            if not isinstance(retrieval[field], str) or not retrieval[field].strip():
                self.error(where, "acquisition requires " + field)
        for field in ("recipe", "driver"):
            self.content_reference(retrieval[field], where + "/retrieval/" + field)
        self.content_references(retrieval["inputs"], where + "/retrieval/inputs")
        receipt = self.content_reference(retrieval["receipt"], where + "/retrieval/receipt", as_json=True)
        fields = "schema_version kind task_id role candidate_manifest_sha256 job_id attempt_id result terminal mode recipe driver inputs images observed_members limits limitations evidence"
        if not self.content_fields(receipt, fields, where + "/receipt"):
            return
        if (type(receipt["schema_version"]) is not int or receipt["schema_version"] != 1
                or receipt["kind"] != "content_acquisition" or receipt["task_id"] != task_id
                or receipt["role"] != role or receipt["candidate_manifest_sha256"] != manifest_sha):
            self.error(where, "acquisition schema/task/role/candidate binding mismatch")
        if receipt["result"] != "succeeded" or receipt["terminal"] is not True or receipt["mode"] != "final_filesystem":
            self.error(where, "terminal successful final-filesystem observation required; partial/selected-layer/overlay proofs unsupported")
        for field in ("job_id", "attempt_id", "recipe", "driver", "inputs"):
            if receipt[field] != retrieval[field]:
                self.error(where, "acquisition receipt differs from frozen " + field)
        if not same_json(receipt["images"], images) or not same_json(receipt["observed_members"], members):
            self.error(where, "acquisition receipt image/member lineage differs from content inventory")
        for field in ("recipe", "driver"):
            self.content_reference(receipt[field], where + "/receipt/" + field)
        self.content_references(receipt["inputs"], where + "/receipt/inputs")
        self.content_references(receipt["evidence"], where + "/receipt/evidence")
        limits = receipt["limits"]
        if self.content_fields(limits, "max_memory_bytes max_cpu_count wall_timeout_seconds network_policy", where + "/limits"):
            for field in ("max_memory_bytes", "max_cpu_count", "wall_timeout_seconds"):
                if type(limits[field]) is not int or limits[field] <= 0:
                    self.error(where, "acquisition limits require positive integer " + field)
            if not isinstance(limits["network_policy"], str) or not limits["network_policy"].strip():
                self.error(where, "acquisition network policy required")
        if not isinstance(receipt["limitations"], str) or not receipt["limitations"].strip():
            self.error(where, "acquisition limitations required")

    def artifact(self, task_id, name, item, manifest, manifest_sha=None, artifacts=None):
        where = task_id + "/artifacts/" + name
        if not isinstance(item, dict) or item.get("status") != "pinned":
            self.error(where, "artifact has not been acquired and pinned")
            return None
        sha = item.get("sha256")
        if not isinstance(sha, str) or not SHA256.fullmatch(sha):
            self.error(where, "immutable artifact SHA256 required")
            return None
        ref = item.get("record")
        record = self.reference(ref, where, as_json=True)
        if not isinstance(ref, dict) or ref.get("sha256") != sha:
            self.error(where, "artifact identity must equal record SHA256")
        if record is None:
            return None
        if name.endswith("_image"):
            role = name.split("_")[0]
            if item.get("source_reference") != manifest.get(role, {}).get("image_tag"):
                self.error(where, "artifact tag differs from current task configuration")
            if item.get("kind") != "oci_manifest" or record.get("schemaVersion") != 2:
                self.error(where, "image requires acquired OCI/Docker schema-2 image manifest")
            descriptors = [record.get("config", {})] + record.get("layers", [])
            if len(descriptors) < 2:
                self.error(where, "resolved platform image config and layers required")
            for descriptor in descriptors:
                value = descriptor.get("digest", "") if isinstance(descriptor, dict) else ""
                if not isinstance(value, str) or not value.startswith("sha256:") or not SHA256.fullmatch(value[7:]):
                    self.error(where, "immutable SHA256 image descriptor required")
            config_ref = item.get("config")
            config = self.reference(config_ref, where + "/config", as_json=True)
            if not isinstance(config_ref, dict) or "sha256:" + str(config_ref.get("sha256")) != record.get("config", {}).get("digest"):
                self.error(where, "config content identity differs from image descriptor")
            if config is not None and config.get("os", "") + "/" + config.get("architecture", "") != manifest.get("platform"):
                self.error(where, "acquired config platform differs from task")
            if item.get("platform") != manifest.get("platform"):
                self.error(where, "image platform differs from task")
        elif item.get("kind") == "content_inventory":
            self.content_fields(item, "kind status sha256 record", where)
            self.content_reference(ref, where)
            self.content_inventory(task_id, name, record, manifest, manifest_sha, artifacts, where)
        else:
            if item.get("kind") != "file_inventory" or record.get("task_id") != task_id or record.get("role") != name:
                self.error(where, "task-specific artifact file inventory required")
            self.references(record.get("files"), where + "/files")
        return sha

    def gate(self, task_id, name, gate, manifest_sha, artifacts):
        where = task_id + "/gates/" + name
        if not isinstance(gate, dict) or gate.get("status") != "passed":
            self.error(where, "not passed")
            return None
        report = self.reference(gate.get("report"), where, as_json=True)
        if report is None:
            return None
        if report.get("task_id") != task_id or report.get("gate") != name or report.get("manifest_sha256") != manifest_sha:
            self.error(where, "report not bound to current task, gate and manifest")
        if report.get("artifact_sha256") != artifacts or None in artifacts.values():
            self.error(where, "report artifact identities do not match acquired artifacts")
        if self.harness_sha256 is None or report.get("harness_sha256") != self.harness_sha256:
            self.error(where, "report not bound to current harness inventory")
        if report.get("result") != "passed" or not report.get("reviewer") or not report.get("method") or not report.get("limitations"):
            self.error(where, "passing report, reviewer, method and explicit limitations required")
        assertions = report.get("assertions", {})
        if not isinstance(assertions, dict):
            self.error(where, "named assertions required")
            return report
        for assertion in REQUIREMENTS[name]:
            check = assertions.get(assertion, {})
            if not isinstance(check, dict) or check.get("result") != "passed" or not check.get("finding"):
                self.error(where, assertion + " has no passing substantiated finding")
            else:
                self.references(check.get("evidence"), where + "/" + assertion)
        return report

    def task(self, task_id, lock):
        where = "audit/tasks/{}.json".format(task_id)
        record = self.read(where, where)
        if record is None:
            return None
        path = "tasks/{}.json".format(task_id)
        manifest = self.read(path, task_id)
        if manifest is None:
            return None
        current_sha = digest(self.root / path)
        if record.get("schema_version") != 1 or record.get("task_id") != task_id or manifest.get("task_id") != task_id:
            self.error(task_id, "task identity/schema mismatch")
        source = record.get("source", {})
        if source.get("manifest_path") != path or source.get("manifest_sha256") != lock["upstream_sha256"][path]:
            self.error(task_id, "upstream manifest identity mismatch")
        for key in ("dataset_revision", "source_revision"):
            if source.get(key) != lock.get(key):
                self.error(task_id, "upstream {} mismatch".format(key))
        candidate = record.get("candidate", {})
        if candidate.get("manifest_path") != path or candidate.get("manifest_sha256") != current_sha:
            self.error(task_id, "candidate manifest changed since review")
        disposition = record.get("disposition", {})
        decision = disposition.get("decision")
        if disposition.get("status") != "reviewed" or decision not in ("retain", "repair", "exclude"):
            self.counts["pending"] += 1
            self.error(task_id, "disposition is pending; no task can disappear from public scope")
        if not disposition.get("rationale"):
            self.error(task_id, "disposition rationale required")
        bundle_sha = review_bundle_hash(record, self.harness_sha256, self.claim_catalog_sha256)
        self.reviews(disposition.get("reviews"), task_id, current_sha, decision, bundle_sha)
        if decision == "retain" and current_sha != source.get("manifest_sha256"):
            self.error(task_id, "retain cannot change upstream task configuration")
        changed = current_sha != source.get("manifest_sha256")
        if changed or decision == "repair":
            changes = candidate.get("changes", [])
            if not isinstance(changes, list) or not changes:
                self.error(task_id, "repairs require explicit changes and evidence")
            else:
                for change in changes:
                    if not isinstance(change, dict) or not change.get("rationale") or not change.get("summary"):
                        self.error(task_id, "each change requires summary and rationale")
                    else:
                        self.references(change.get("evidence"), task_id + "/changes")
        claims = record.get("claims")
        if not isinstance(claims, list):
            self.error(task_id, "explicit claims list required, possibly empty")
        else:
            observed = [{key: item.get(key) for key in ("claim_id", "path", "sha256")} for item in claims if isinstance(item, dict)]
            expected = list(self.claims_by_task.get(task_id, {}).values())
            if sorted(observed, key=lambda item: str(item["claim_id"])) != sorted(expected, key=lambda item: str(item["claim_id"])):
                self.error(task_id, "task claim references must exactly cover the applicability catalog")
            for item in claims:
                claim = self.reference(item, task_id + "/claims", as_json=True)
                if claim is None:
                    continue
                if not item.get("claim_id") or item.get("claim_id") != claim.get("claim_id"):
                    self.error(task_id, "claim ID differs from referenced report")
                impact = item.get("impact", {})
                if decision in ("retain", "repair"):
                    if impact.get("status") not in ("resolved", "not_applicable") or not impact.get("rationale"):
                        self.error(task_id, "claim task impact remains unresolved")
                    else:
                        self.references(impact.get("evidence"), task_id + "/claim-impact")
        if decision == "exclude":
            self.counts["excluded"] += 1
            self.references(disposition.get("exclusion_evidence"), task_id + "/exclusion")
            return "excluded"
        if decision in ("retain", "repair"):
            self.counts["included"] += 1
        artifacts = record.get("artifacts", {})
        identities = {name: self.artifact(task_id, name, artifacts.get(name), manifest, current_sha, artifacts) for name in ARTIFACTS}
        reports = {name: self.gate(task_id, name, record.get("gates", {}).get(name), current_sha, identities) for name in REQUIREMENTS}
        execution, independent = reports.get("execution"), reports.get("independent_reproduction")
        if execution and independent:
            if execution.get("reviewer") == independent.get("reviewer") or execution.get("method") == independent.get("method"):
                self.error(task_id, "independent reproduction must use a different reviewer and method")
            refs = [record["gates"][name]["report"]["sha256"] for name in ("execution", "independent_reproduction")]
            if refs[0] == refs[1]:
                self.error(task_id, "independent reproduction cannot reuse execution report")
        return "included" if decision in ("retain", "repair") else "pending"

    def run(self):
        registry = self.read("audit/task-registry.json", "registry")
        lock = self.read("audit/upstream-lock.json", "upstream-lock")
        if registry is None or lock is None:
            return self.result()
        if registry.get("schema_version") != 1 or registry.get("scope") != SCOPE:
            self.error("registry", "scope must account for all 51 public and 83 unavailable tasks; no 134-task certification")
        if registry.get("upstream_lock_sha256") != digest(self.root / "audit/upstream-lock.json"):
            self.error("registry", "upstream lock changed since registry construction")
        self.harness(registry.get("release", {}).get("harness_inventory"))
        mapping = lock.get("upstream_sha256", {})
        task_paths = [name for name in mapping if re.fullmatch(r"tasks/[a-z0-9_]+\.json", name)]
        locked_ids = sorted(Path(name).stem for name in task_paths)
        self.counts["public"] = len(locked_ids)
        if len(locked_ids) != PUBLIC_TASKS:
            self.error("upstream-lock", "must preserve all 51 original public manifest identities")
        if registry.get("task_ids") != locked_ids:
            self.error("registry", "task IDs must exactly match all locked public tasks, sorted without duplicates")
        self.claim_catalog(registry.get("claim_catalog"), locked_ids)
        for directory in ("tasks", "audit/tasks"):
            actual = sorted(path.stem for path in (self.root / directory).glob("*.json"))
            if actual != locked_ids:
                self.error(directory, "file IDs differ from public task scope")
        included, excluded = [], []
        for task_id in locked_ids:
            result = self.task(task_id, lock)
            if result == "included":
                included.append(task_id)
            elif result == "excluded":
                excluded.append(task_id)
        release = registry.get("release", {})
        if release.get("status") != "candidate":
            self.error("release", "release is not explicitly a candidate")
        if release.get("included_task_ids") != included or release.get("excluded_task_ids") != excluded:
            self.error("release", "release inclusion/exclusion must exactly match reviewed dispositions")
        if not included:
            self.error("release", "empty verified benchmark is not a publishable release")
        if len(included) + len(excluded) != PUBLIC_TASKS:
            self.error("release", "all 51 public tasks need completed dispositions")
        return self.result()

    def result(self):
        return {"ready": not self.errors, "counts": self.counts, "errors": self.errors,
                "meaning": "Evidence-integrity checks only; scientific correctness and reviewer independence require substantive review."}


def check_release(root):
    checker = ReleaseCheck(root)
    try:
        return checker.run()
    except (KeyError, TypeError, AttributeError, ValueError, OSError) as exc:
        checker.error("schema", "malformed or unreadable input: {}".format(exc))
        return checker.result()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--json", action="store_true", help="emit machine-readable full diagnostics")
    args = parser.parse_args()
    result = check_release(args.root)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print("READY" if result["ready"] else "NOT READY")
        print(json.dumps(result["counts"], sort_keys=True))
        for message in result["errors"]:
            print("- " + message)
        print(result["meaning"])
    return 0 if result["ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
