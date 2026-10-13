# Opt-in final grading drain repair

The pinned upstream harness stops waiting after 900 seconds and can return a score before a valid Warehouse evaluation finishes (one saved evaluation took 1825.2 seconds). This host-side repair is required alongside the Warehouse judge image to address that integration gap. It is a separate opt-in overlay: `sforge/` and `tasks/` in this repository remain byte-for-byte upstream.

The patched harness stops and joins the automatic submission producer (450-second operational join bound), then polls authoritative full history until no recorded submissions are running or queued. It uses that terminal history directly to construct the final result, rather than making a second fallible request. Its operational deadline is 300 seconds plus `eval_timeout + 300` seconds for each distinct pending submission observed. Each new submission adds that allowance once. This accounts for serial queue service, not just one evaluation. It does not assert that backend provisioning or external contention always fits the allowance. A deadline or three consecutive history errors raises `FinalDrainError` on every backend; a partial score is not returned as a completed result.

## Use

From the repository root, choose a new output directory:

```bash
python3 repairs/harness-final-drain-v1/materialize.py /tmp/ebv-final-drain
cd /tmp/ebv-final-drain
PYTHONPATH=/tmp/ebv-final-drain python3 -m sforge --help
```

Run the desired harness command from this materialized directory, with absolute paths to the task/configuration and the normal harness dependencies installed. This copies the full source package and applies the source-locked patch; it does not build a judge image, install dependencies, or change task JSON. The script refuses an existing output directory. The normal upstream CLI from the original checkout will **not** apply this repair.

## Validation and limits

```bash
python3 repairs/harness-final-drain-v1/test_drain.py
python3 tools/check_upstream.py
```

The tests materialize the patch, compile the resulting Python, execute its real drain function with deterministic clock/HTTP substitutes, execute the real final-result assembly, and execute the actual exception-propagation guard. A paired upstream control returns at 900 seconds with the evaluation still running and score 0; the same 1825.2-second fixture under the overlay reaches terminal history and preserves score 42. These scores are synthetic fixtures, not Warehouse benchmark scores. Controls cover empty history, the 1825.2-second Warehouse duration, three serial jobs completing after 10500 seconds, transient faults, HTTP errors, malformed history, persistent faults and a stalled-job deadline. The latter fails at 4200 seconds for one 3600-second job. These are component and caller-wiring tests, **not** an end-to-end Docker/Kubernetes/model run. Existing Warehouse judge controls are unchanged.

A backend may exceed the operational bound; this then fails visibly and requires diagnosis rather than silently dropping pending reports. The overlay does not repair a hung judge or recover results after process termination. Work-container processes and the auto-eval producer are stopped before draining; already accepted jobs are tracked through history. There is no new judge-server admission barrier for an HTTP submission already in flight but not yet registered. Manual user interruption retains upstream interruption behavior and can return partial results labeled interrupted.

### Producer shutdown follow-up

The overlay now checks producer cancellation before archive creation and again before starting the transfer phase. Its local archive cleanup requests a 15-second command timeout instead of using the backend's default command timeout. A paired test executes the real extraction caller with a fake E2B backend: cancellation during a 250-second initial tar previously continued into a second 250-second wrapper tar, exceeding the join allowance; the patched caller exits after the first phase and never starts the wrapper tar. An uninterrupted extraction still returns the same payload.

The 450-second join is an operational limit, not a proven upper bound for every backend. Cancellation arriving during E2B's wrapper tar or a blocking download is still subject to the existing backend's cancellation checks and transfer behavior; its internal temporary-file cleanup and transport latency are not bounded by this host overlay. A sufficiently delayed backend can therefore still cause a visible `FinalDrainError`. These tests use deterministic fake I/O and do not establish native shutdown timing.
