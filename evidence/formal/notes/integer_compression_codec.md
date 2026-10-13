# integer_compression_codec (formula maximum and fixed score scale)

## Claim

1. The per-dataset score is S = min(c, 8)·min(s, 40), with c, s ≥ 0. It satisfies S ≤ 320, and
   S = 320 exactly when c ≥ 8 and s ≥ 40.
2. The weighted composite uses weights 2, 1.5, 1.5, 1, 1, 1, 1, 1 (Σ = 10), and a failed dataset
   scores 0. The composite is ≤ 320, and it equals 320 only when every dataset scores 320,
   that is, when every dataset is at both caps.
3. The fixed scale linear(1, 320) maps 1 → 0 and 320 → 100, and it does not clip on [1, 320].
4. The regraded Opus 5.5 composite 160.76388698076738 is the weighted mean of its eight printed
   per-dataset scores, and its value on the fixed scale is 50.0827….

## Model and link to the code

`Ebv/IntCodecScale.lean` (output `IntCodecScale.out`). It models the fixed `runner_judge.py`
(sha256 `f205adb8…e152`): DATASETS on lines 25–34 and `compute_total_score` on lines 115–128.
The formula and weights are the same as in the original. The scale functions model
`score_rescale.py` lines 60–63 and 80–84. Inputs come from
`evidence/runs/opus55-regrade/result/out/logs/ic-agent-20-v2.raw.txt`.

## Result

**Proved.**
- The exact weighted mean of the printed scores is 200954858725959231/1250000000000000. It
  differs from the printed composite by 4.8e-15, which is double rounding.
- On the fixed scale, the printed composite scores exactly 7988194349038369/159500000000000
  ≈ 50.08272.
- Differential check from the raw log fields (encoded bytes, n, decode_gbps of the submission
  and of the starter): ts_sec is at both caps (320), and sparse equals 8·32.4063/0.85 to
  within 1e-12.
- The other published fixed-scale values also reproduce: 0.9786 → 0, 1.0155 → 0.00,
  6.7024 → 1.79, 6.9708 → 1.87 and 114.19 → 35.48.

## Counter-check

`counter_orig_clips`: linear(0, 100) maps 160.76 to 100, and `counter_orig_ties` shows that
114.19 also maps to 100, so the two tie. `counter_bound_319`: a bound of 319 is false.
`counter_one_below_cap`: S(7.99, 40) < 320.

## Limits

- The proofs use exact rationals instead of doubles. The `max(·, 1e-9)` guards are dropped, and
  ratios are assumed non-negative.
- The proofs do not cover the timing noise of the measured starter baseline, or whether 320
  can be reached in practice.
- The fix's main change, taking `B_i^0` and `T_i^0` from the starter measured in the same run
  instead of from `baseline_results.json`, is not modelled. The theorems hold equally for the
  original grader with the new scale. That change rests on the paired runs.
- Any composite below 1.0 (worse than the starter) is clipped to 0 on the fixed scale. This is
  by design, not a defect.
