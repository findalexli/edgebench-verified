# EdgeBench's leaderboard configuration: grader CPUs and memory

Several findings depend on how many CPUs EdgeBench's leaderboard gives each grader. This page quotes
the relevant lines of EdgeBench's own configuration files, so that the premise can be checked here.

## Source

EdgeBench's public GitHub repository at commit `6e4e5f4aa087a9121aa09a6059e5484e5102c6ff` (the commit
`sforge/` is taken from), directory `examples/all-tasks-k8s/`. EdgeBench's files are Apache-2.0
(`LICENSE`). Each file was downloaded from `raw.githubusercontent.com` and its sha256 compared with
the copy in EdgeBench's source distribution; they are identical.

| File | Header line 1 | sha256 |
| --- | --- | --- |
| [`experiment.yaml`](https://github.com/ByteDance-Seed/EdgeBench/blob/6e4e5f4aa087a9121aa09a6059e5484e5102c6ff/examples/all-tasks-k8s/experiment.yaml) | `# OFFICIAL EDGEBENCH LEADERBOARD SETTING (Claude Code + Claude models)` | `d9d299794ba946cae8d2b7f68a7879a35bb8565d95e78107edf79802993643be` |
| [`experiment-codex.yaml`](https://github.com/ByteDance-Seed/EdgeBench/blob/6e4e5f4aa087a9121aa09a6059e5484e5102c6ff/examples/all-tasks-k8s/experiment-codex.yaml) | `# OFFICIAL EDGEBENCH LEADERBOARD SETTING (Codex + GPT)` | `6cf7d41bc67f765adbd458409209e6af02bbb9a53020cf366511707b3fc45b33` |
| [`experiment-deepseek.yaml`](https://github.com/ByteDance-Seed/EdgeBench/blob/6e4e5f4aa087a9121aa09a6059e5484e5102c6ff/examples/all-tasks-k8s/experiment-deepseek.yaml) | `# OFFICIAL EDGEBENCH LEADERBOARD SETTING (Claude Code + DeepSeek V4 Pro)` | `35f09b33bc36d74f57be1e88920b3bf1a48f9950c15ac91784d25d76f7df47e5` |
| [`experiment-glm.yaml`](https://github.com/ByteDance-Seed/EdgeBench/blob/6e4e5f4aa087a9121aa09a6059e5484e5102c6ff/examples/all-tasks-k8s/experiment-glm.yaml) | `# OFFICIAL EDGEBENCH LEADERBOARD SETTING (Claude Code + GLM 5.1)` | `b7b7c2de7575689c2e9c4287d50b5d7ce0da43e52b05477152ec6c45d141f694` |

Lines 2–4 of each file read: "The experiment YAMLs in this directory are the official settings /
behind the leaderboard numbers. For comparable results, change only / `env`, `model`, and registry
values."

The four files set the same `defaults` block and the same per-task overrides. They differ only in the
agent (`codex` instead of `claude-code`) and in model environment variables (`extra_env`). Whether
every leaderboard run used these files exactly is not documented beyond this header.

## The relevant lines (`experiment.yaml`; the other three files have the same values)

Defaults applied to every task (lines 42–51):

```yaml
defaults:
  backend: k8s
  agent: claude-code
  timeout: 43200                          # 12 hours per task
  eval_interval: 1800                     # auto-eval every 30 min
  submission_cooldown: 120                # min seconds between agent submissions
  work_cpu_limit: 4
  work_mem_limit: "16g"
  judge_cpu_limit: 4
  judge_mem_limit: "8g"
```

The override for Lean and Coq tasks (lines 54–59):

```yaml
# Lean/Coq theorem-proving tasks need more CPU and memory for the prover.
x-lean-task: &lean_task
  work_cpu_limit: 8
  work_mem_limit: "16g"
  judge_cpu_limit: 8
  judge_mem_limit: "16g"
```

The only other CPU override (lines 98–102):

```yaml
  smt_solver:
    work_cpu_limit: 16
    work_mem_limit: "16g"
    judge_cpu_limit: 16
    judge_mem_limit: "16g"
```

The tasks whose grader runs several cases at once under a wall-clock limit (lines 76, 78, 92, 94,
96, 103, 105, 107, 108 and 130, shown here in that order):

```yaml
  exchange_core_throughput: {}
  git_rewrite_in_zig: {}
  apple_incremental_game: {}
  grid_turing_robot: {}
  molecular_self_assembly: {}
  treant_forest: {}
  triangulation_coloring_optimization: {}
  vibrating_path_graph_coloring: {}
  warehouse_forklift_routing: {}
  dcss_dungeon_ai: {}
```

`{}` means the task "inherits all defaults" (line 63).

## What follows

- **The grader gets 4 CPUs by default.** No task in any of the four files sets a lower value.
- **Fixed for their CPU share:** Apple Game, Grid Robot, Molecular Assembly, Triangulation, Vibrating
  Path and Warehouse Routing. They have no override in any of the four files, so their graders get
  4 CPUs while running 8 cases at once.
- **CPU aspect recorded as a note only:** Exchange Core, Treant Forest, Git in Zig and DCSS have no
  override either, so their graders also get 4 CPUs. Exchange Core, Treant Forest and Git in Zig are
  fixed tasks, for other problems; only their CPU aspect is a note. DCSS is kept with a note.
- **SMT Solver** is set to 16 grader CPUs in all four files. Its grader runs 16 solver processes at
  once, so each gets one CPU, and the CPU-share problem does not arise in the leaderboard setting.
- **Seven Lean tasks** use `*lean_task` (8 grader CPUs, 16 GB): carleson_formalization,
  combinatorial_games_formalization, flt_regular_formalization, lean_analysis_proofs,
  new_foundations_consistency, pfr_formalization and sphere_eversion_formalization.
  ordinal_notation_well_foundedness uses the defaults. None of these tasks has a CPU finding.
- **How the value reaches the grader.** The per-task value overrides the default
  (`sforge/harness/experiment.py:262-265`). The harness passes it to the grader container
  (`sforge/harness/run_evaluation.py:164`). The Kubernetes backend sets it as the container's CPU
  request and limit (`sforge/harness/backend/k8s_backend.py:214-219`). Without a configuration file, `judge_cpu_limit` is `None` (`sforge/harness/config.py:69`), and
  the task JSON's own `judge.cpu_limit` applies; none of the public task JSONs sets one.
