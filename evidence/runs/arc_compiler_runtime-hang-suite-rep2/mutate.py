"""Apply one arm's edit to the starter's compiler/src/runtime.js (exact string replacement, asserted).
Usage: python mutate.py <arm> <path to runtime.js>.  Arms: a_starter, t_hang, t_throw."""
import sys
arm, path = sys.argv[1], sys.argv[2]
src = open(path).read()
OLD = 'return "`" + inner.replace(/`/g, "\\\\`").replace(/\\{([^}]+)\\}/g, (_, e) => "${" + compileExpr(e) + "}") + "`";'
NEW = 'return "`" + inner.replace(/`/g, "\\\\`").replace(/\\{([^}]+)\\}/g, (_, e) => "${" + compileExpr(scanInterpolation(e)) + "}") + "`";'
SCAN = '''// Walk an embedded interpolation expression so index groups like items[0] are kept together.
function scanInterpolation(e) {
  let j = 0;
  while (j < e.length) {
    if (e[j] === "[") %s
    j++;
  }
  return e;
}

'''
BODY = {
    't_hang': '{ j = e.indexOf("[", j); continue; } // BUG (typo): meant e.indexOf("]", j) + 1',
    't_throw': 'throw new Error("diagnostic: index inside interpolation");',
}
if arm == 'a_starter':
    print('no mutation')
    sys.exit(0)
assert src.count(OLD) == 1, 'anchor not found'
anchor = 'function convertRanges(s) {'
assert src.count(anchor) == 1
src = src.replace(OLD, NEW).replace(anchor, SCAN % BODY[arm] + anchor)
open(path, 'w').write(src)
print('patched', arm)
