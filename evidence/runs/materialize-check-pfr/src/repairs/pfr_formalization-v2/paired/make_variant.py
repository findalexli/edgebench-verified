#!/usr/bin/env python3
"""Build one paired-run submission from a starter PFR/WeakPFR.lean (original or fixed version).

Usage: make_variant.py {v1|v2} {starter|T|D|BAD} WeakPFR.lean   (edits the file in place)

The added lemmas are the same in both versions. The only difference is where the measure binders
come from, which mirrors how each version states the five affected targets:
  v1: the section `variable (μ : Measure Ω := by volume_tac) ... [IsProbabilityMeasure μ] ...`;
  v2: the same binders written at the start of the lemma's own signature (as the fixed file does).

  starter  unchanged starter.
  T        trigger: two fully proved (rfl) lemmas stated exactly like the five targets
           (one in section Torsion, one in section F2_projection).
  D        T plus a downstream lemma, identical text in v1 and v2, outside both sections, with
           ordinary measure binders, whose proof applies `ebv_trig_f2`.
  BAD      bad control: target `app_ent_PFR` proved from the still-sorried `app_ent_PFR'`
           (the upstream proof), plus a new lemma proved by `sorry`.
"""
import sys

version, variant, path = sys.argv[1:]
assert version in ('v1', 'v2') and variant in ('starter', 'T', 'D', 'BAD')
s = open(path, encoding='utf-8').read()

BINDERS = {'v1': '', 'v2': "(μ : Measure Ω := by volume_tac) (μ' : Measure Ω' := by volume_tac)\n"
                          "    [IsProbabilityMeasure μ] [IsProbabilityMeasure μ']\n    "}[version]


def insert_before(anchor, text):
    global s
    assert s.count(anchor) == 1, anchor
    s = s.replace(anchor, text + anchor)


def replace(old, new):
    global s
    assert s.count(old) == 1, old
    s = s.replace(old, new)


if variant in ('T', 'D'):
    insert_before('end Torsion\n',
                  '/-- ebv trigger: fully proved, stated like `torsion_free_doubling` -/\n'
                  'lemma ebv_trig_torsion ' + BINDERS + '[FiniteRange X] (hX : Measurable X) :\n'
                  "    d[X; μ # Y; μ'] = d[X; μ # Y; μ'] := rfl\n\n")
    insert_before('end F2_projection\n',
                  '/-- ebv trigger: fully proved, stated like `PFR_projection` -/\n'
                  'lemma ebv_trig_f2 ' + BINDERS + '(hX : Measurable X) :\n'
                  "    H[X; μ] + H[Y; μ'] = H[X; μ] + H[Y; μ'] := rfl\n\n")
if variant == 'D':
    replace('end F2_projection\n',
            'end F2_projection\n\n'
            'open MeasureTheory ProbabilityTheory in\n'
            '/-- ebv downstream: fully proved, ordinary binders, applies `ebv_trig_f2` -/\n'
            'lemma ebv_down_f2 {G Ω Ω\' : Type*} [AddCommGroup G] [Module (ZMod 2) G] [Finite G]\n'
            '    [MeasurableSpace G] [MeasurableSingletonClass G] [MeasurableSpace Ω] [MeasurableSpace Ω\']\n'
            '    (X : Ω → G) (Y : Ω\' → G) (ν : Measure Ω) (ν\' : Measure Ω\') [IsProbabilityMeasure ν]\n'
            '    [IsProbabilityMeasure ν\'] (hX : Measurable X) :\n'
            '    H[X; ν] + H[Y; ν\'] = H[X; ν] + H[Y; ν\'] :=\n'
            '  ebv_trig_f2 X Y ν ν\' hX\n')
if variant == 'BAD':
    # app_ent_PFR: its own `sorry` replaced by the upstream proof through app_ent_PFR' (still sorried)
    start = s.index('lemma app_ent_PFR ')
    body = s.index(':= by\n  sorry\n', start)
    s = (s[:body] + ':= by\n  let _ : MeasureSpace Ω := ⟨μ⟩\n  let _ : MeasureSpace Ω\' := ⟨μ\'⟩\n'
         '  exact app_ent_PFR\' X Y hent hX hY\n' + s[body + len(':= by\n  sorry\n'):])
    insert_before('end F2_projection\n',
                  '/-- ebv bad control: proved by `sorry` -/\n'
                  'lemma ebv_bad_sorry ' + BINDERS + '(hX : Measurable X) : H[X; μ] = 0 := by\n'
                  '  sorry\n\n')
open(path, 'w', encoding='utf-8').write(s)
