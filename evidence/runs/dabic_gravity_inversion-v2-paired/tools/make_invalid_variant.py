"""Invalid control: the data-form D-ABIC directive with the log-determinant computed by
np.linalg.det (which overflows for these spectra) instead of the stable log1p sum.
Usage: python3 -I make_invalid_variant.py <dabic_directive_data.py> <out.py>"""
import sys
src = open(sys.argv[1], encoding="utf-8").read()
old = "abic.append(f + float(np.sum(np.log1p(ev / b))))"
new = "abic.append(f + float(np.log(np.linalg.det(np.eye(len(ev)) + np.diag(ev / b)))))"
assert src.count(old) == 1
open(sys.argv[2], "w", encoding="utf-8").write(src.replace(old, new))
