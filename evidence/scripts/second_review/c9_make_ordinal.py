#!/usr/bin/env python3
"""Job for the ordinal helper-name claim. The closed task1 proof is our own (evidence/scripts/ordinal_notation_well_foundedness/sub_helper):
no real solver archive exists for this task. Only the helper's file name and its import differ between control and trigger."""
import io, os, sys, tarfile
sys.path.insert(0, os.path.dirname(__file__))
from c9_jobs_common import job_dir
T = 'ordinal_notation_well_foundedness'
UP = sys.argv[1]
E = 'evidence/scripts/ordinal_notation_well_foundedness/'
task1 = open(E + 'sub_helper/task1.v', 'rb').read(); helper = open(E + 'sub_helper/OrdHelpers.v', 'rb').read()
axiom = open(E + 'sub_controls/task3.v', 'rb').read()
def t1(name):
    assert task1.count(b'OrdHelpers') == 1
    return task1.replace(b'OrdHelpers', name.encode())
def tar(path, files):
    with tarfile.open(path, 'w:gz') as t:
        for n, b in files.items():
            ti = tarfile.TarInfo(n); ti.size = len(b); ti.mode = 0o644
            t.addfile(ti, io.BytesIO(b))
broken = b"(* scratch notes, left over *)\nLemma scratch : 1 = 2.\nProof. reflexivity. Qed.\n"
toml = f'edgebench/tasks/{T}/task.toml'
old = open(UP + '/' + toml).read()
a = '  "eval_task*.v", "ChildOf.v", "debug*.v", "test*.v", "check*.v", "explore*.v", "tmp*.v", "scratch*.v",\n'
b = '  "eval_task*.v", "ChildOf.v",\n'
assert old.count(a) == 1
i = old.split('\n').index(a.rstrip('\n')) + 1
n = old.count('\n')
patch = (f'diff --git a/{toml} b/{toml}\n--- a/{toml}\n+++ b/{toml}\n@@ -{i-1},3 +{i-1},3 @@\n'
         + ' ' + old.split('\n')[i-2] + '\n' + '-' + a + '+' + b + ' ' + old.split('\n')[i] + '\n')
arms = r'''# sforge eval, so the archive filter runs. Three passes, order reversed each pass. cpus=4 from task.toml.
for pass in 1 2 3; do o="old new"; [ $pass = 2 ] && o="new old"
  for arm in helper_ok helper_check helper_test inline axiom scratch_broken; do for sd in $o; do seval $arm-p$pass $sd $arm.tar.gz 60; done; done
done
for sd in old new; do grade starter-p1 $sd empty 60; done
'''
d = job_dir('community9-' + T, T, 'Ordinal helper-name exclusions; new = name patterns removed from submission.exclude.', 2900, patch, arms)
s = d + '/subs/'
tar(s + 'helper_ok.tar.gz', {'ZeroHelpers.v': helper, 'task1.v': t1('ZeroHelpers')})
tar(s + 'helper_check.tar.gz', {'check_zero.v': helper, 'task1.v': t1('check_zero')})
tar(s + 'helper_test.tar.gz', {'test_lemmas.v': helper, 'task1.v': t1('test_lemmas')})
tar(s + 'inline.tar.gz', {'task1.v': open(E + 'sub_controls/task1.v', 'rb').read()})
tar(s + 'axiom.tar.gz', {'ZeroHelpers.v': helper, 'task1.v': t1('ZeroHelpers'), 'task3.v': axiom})
tar(s + 'scratch_broken.tar.gz', {'ZeroHelpers.v': helper, 'task1.v': t1('ZeroHelpers'), 'check_scratch.v': broken})
print(d); print(patch)
