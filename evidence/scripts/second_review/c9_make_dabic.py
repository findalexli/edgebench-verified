#!/usr/bin/env python3
"""Jobs for the DABIC data-space gate claim. Real best r2 auto-35, unchanged; the same directive with only its determinant work moved to the M x M
model-space matrix (same eigenvalues, same beta path up to rounding); and that form with beta left alone (bad control). results.json and report.md stay identical."""
import difflib, os, shutil, sys
sys.path.insert(0, os.path.dirname(__file__))
from c9_jobs_common import job_dir, real_archive, rewrite, sub_once
T = 'dabic_gravity_inversion'
UP = sys.argv[1]; mode = sys.argv[2]
M = 'outputs/dabic_directive.py'
DATA = b"""        B = WJF @ X
        B = 0.5 * (B + B.T)
        lam, V = np.linalg.eigh(B)
        lam = np.clip(lam, 0.0, None)
"""
MODEL = b"""        # Model-space form: |F| x |F| matrix H = L^-1 J^T J L^-T with Q_FF = L L^T. Its top N eigenpairs
        # give the same log|I + B/beta| and the same data-space eigenvectors V = C^T U / sqrt(lam).
        L = np.linalg.cholesky(QFF.toarray())
        C = solve_triangular(L, WJF.T, lower=True)
        H = C @ C.T
        lam_m, U_m = np.linalg.eigh(0.5 * (H + H.T))
        lam = lam_m[-N:]
        V = (C.T @ U_m[:, -N:]) / np.sqrt(np.clip(lam, 1e-300, None))
        lam = np.clip(lam, 0.0, None)
"""
IMP = b"from scipy.sparse.linalg import splu\n"
IMP2 = IMP + b"from scipy.linalg import solve_triangular\n"
KEEP = (b"        self.invProb.beta = beta\n        self.beta_history.append(beta)\n",
        b"        self.beta_history.append(self.invProb.beta)\n")
def model(b): return sub_once(sub_once(b, DATA, MODEL), IMP, IMP2)
def const(b): return sub_once(model(b), *KEEP)
p = f'edgebench/tasks/{T}/judge/eval_dabic_v2.py'
old = open(UP + '/' + p).read()
new = old
for a, b in (
 ("""        structural_failure = (not is_data_space) or (not beta_truly_updated) or uses_bad_det\n""",
  """        # The task lets the solver pick the model-space or the data-space form; either dimension counts.
        is_model_space = (
            len(square_dims) > 0
            and n_cell_match >= max(1, len(square_dims) // 2)
            and n_cell_match > n_data_match
        )
        known_space = is_data_space or is_model_space
        structural_failure = (not known_space) or (not beta_truly_updated) or uses_bad_det\n"""),
 ("""        if is_data_space:        e1_raw += 4.0\n""", """        if known_space:          e1_raw += 4.0\n"""),
 ("""            "is_data_space": is_data_space,\n""", """            "is_data_space": is_data_space,\n            "is_model_space": is_model_space,\n"""),
):
    assert new.count(a) == 1, a
    new = new.replace(a, b)
patch = f'diff --git a/{p} b/{p}\n' + ''.join(difflib.unified_diff(old.splitlines(True), new.splitlines(True), f'a/{p}', f'b/{p}'))
A_SMOKE = '''seval auto35-p0 old auto35.tar.gz 300
seval auto35_model-p0 old auto35_model.tar.gz 1200
'''
A_MAIN = '''# sforge eval (timeouts matter): cpus=4, SFORGE_CPUS=4. Three passes, order reversed on the second.
for pass in 1 2 3; do o="old new"; [ $pass = 2 ] && o="new old"
  for arm in auto35 auto35_model auto35_const; do e=120; [ $arm != auto35 ] && e=600; for sd in $o; do seval $arm-p$pass $sd $arm.tar.gz $e; done; done
done
'''
A_BAD = '''# Bad controls for the fix: model-space with np.linalg.det (the gate must keep failing it) and data-space with beta left alone.
for pass in 1 2; do o="old new"; [ $pass = 2 ] && o="new old"
  for arm in auto35_baddet auto35_dconst; do for sd in $o; do seval $arm-p$pass $sd $arm.tar.gz 600; done; done
done
'''
name, arms, lim = {'smoke': ('community9-dabic_gravity_inversion-smoke', A_SMOKE, 1700), 'main': ('community9-dabic_gravity_inversion-a', A_MAIN, 3150), 'bad': ('community9-dabic_gravity_inversion-b', A_BAD, 3000)}[mode]
d = job_dir(name, T, 'DABIC model-space gate.', lim, patch, arms, only='base' if mode == 'smoke' else 'both')
a35 = real_archive(T, '-r2', 'auto-35')
shutil.copy(a35, d + '/subs/auto35.tar.gz')
rewrite(a35, d + '/subs/auto35_model.tar.gz', {M: model})
rewrite(a35, d + '/subs/auto35_const.tar.gz', {M: const})
BADDET = (b"        lam_m, U_m = np.linalg.eigh(0.5 * (H + H.T))\n", b"        lam_m, U_m = np.linalg.eigh(0.5 * (H + H.T))\n        _ = np.linalg.det(H)\n")
rewrite(a35, d + '/subs/auto35_baddet.tar.gz', {M: lambda b: sub_once(model(b), *BADDET)})
rewrite(a35, d + '/subs/auto35_dconst.tar.gz', {M: lambda b: sub_once(b, *KEEP)})
print(d)
