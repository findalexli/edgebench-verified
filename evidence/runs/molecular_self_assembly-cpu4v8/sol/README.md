# Test solutions for this job (not stored here)

The solution files of this job are not kept in the repository, because each one contains the task's shipped
baseline `solution.py` verbatim, and files from the EdgeBench images are not redistributed here.

Each file was made the same way: a one-line comment naming the control, a fixed CPU-work preamble (below), then the shipped baseline
`solution.py` taken unchanged from the pinned grader image
(`seededge/edgebench.judge.molecular_self_assembly@sha256:8afd932de7e5…6da5`, `/home/workspace/molecules/solution.py`,
sha256 `886557ad04df…765e`), then one closing line that logs the end time and CPU time. The preamble and the
closing line do not change the solution's output; they only spend time and write to `/ebvtiming/`, which the
grader does not read. The sha256 of every file as run is in `../result/out/solutions_sha.txt`.

Preamble for `cpuN.py` (`N` = 12, 16, 20, 28):

```python
import sys, io, os, time
_w0 = time.time(); _c0 = time.process_time()
_data = sys.stdin.read()
_log = open(f'/ebvtiming/{os.getpid()}.txt', 'w')
_log.write(f'start {_w0:.3f} {_data.split(chr(10))[0].strip()}\n'); _log.flush()
while time.process_time() - _c0 < N:  # fixed N s of single-thread CPU work
    pass
sys.stdin = io.StringIO(_data)
```

For `wall25.py` the loop is instead `while time.time() - _w0 < 25.0:` (work until a 25 s wall-clock deadline).

After the baseline:

```python
_log.write(f'end {time.time():.3f} cpu {time.process_time() - _c0:.3f}\n'); _log.close()
```

| File | Work before the baseline | sha256 (first 16 hex) |
| --- | --- | --- |
| `cpu12.py` | 12 s of CPU per case | `26262f28b05f2d9d` |
| `cpu16.py` | 16 s of CPU per case | `8f8481950aee3556` |
| `cpu20.py` | 20 s of CPU per case | `9ad1c7b53ac76522` |
| `cpu28.py` | 28 s of CPU per case | `7a907873e5657eb5` |
| `wall25.py` | until 25 s of wall-clock time | `6ca5973585248321` |
