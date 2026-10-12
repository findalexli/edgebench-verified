"""Check selected inputs, or inspect a completed ordinary CLI report. No execution."""
import argparse, hashlib, json, math, pathlib, re, tarfile
P = pathlib.Path(__file__).resolve().parent
ROOT = P.parents[1]
def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()
def check_inputs():
    binding = json.loads((P / 'bindings.json').read_text())
    for row in binding['files']:
        p = ROOT / row['path']
        assert p.stat().st_size == row['bytes'] and digest(p) == row['sha256'], row['path']
    inventory = json.loads((ROOT / 'evidence/selected/maintained-core-runtime-inventory.json').read_text())
    for row in inventory['files']:
        assert digest(ROOT / row['path']) == row['sha256'], row['path']
    with tarfile.open(P / 'controls.tar.gz', 'r:gz') as archive:
        members = archive.getmembers()
        assert len(members) == 3
        for member in members:
            assert member.isfile() and '..' not in pathlib.PurePosixPath(member.name).parts
            assert member.name.startswith('ann_benchmarks/algorithms/custom/')
            assert archive.extractfile(member).read() == (P / 'controls' / member.name).read_bytes()
    print('PASS: selected inputs, 63 maintained source files, and three archive members match.')
def check_report(path):
    assert path.stat().st_size <= 1048576
    report = json.loads(path.read_text())
    output = path.with_name('test_output.txt')
    assert output.stat().st_size <= 1048576
    text = output.read_text()
    cases = re.findall(r'^CASE (\S+) (OK|WA|RE|TLE|CE) score=(\d+)(?:\s+#.*)?$', text, re.M)
    assert len(cases) == 2 and sorted(c[1] for c in cases) == ['OK', 'WA'], cases
    positive = next(int(c[2]) for c in cases if c[1] == 'OK')
    assert positive > 0 and next(int(c[2]) for c in cases if c[1] == 'WA') == 0
    for label, expected in [('CASES_TOTAL', 2), ('CASES_OK', 1), ('TOTAL_SCORE', positive)]:
        values = re.findall(r'^' + label + r'[ \t]+(\d+)[ \t]*$', text, re.M)
        assert len(values) == 1 and int(values[0]) == expected, (label, values)
    assert report['total_tests'] == 2 and report['passed'] == 1 and report['failed'] == 1
    assert report['pass_rate'] == .5 and report['valid'] is True and report['timed_out'] is False
    assert report['score'] == positive
    expected = max(0, min(100, 100 * math.log(positive / 3108) / math.log(21472 / 3108)))
    assert abs(report['score_0_100'] - expected) < 1e-10
    print(json.dumps({'result': 'PASS', 'raw_qps': positive, 'normalized_score': expected,
                      'scope': 'Two declared controls; not model performance or full task certification.'}))
if __name__ == '__main__':
    args = argparse.ArgumentParser()
    args.add_argument('--report', type=pathlib.Path)
    options = args.parse_args()
    check_report(options.report) if options.report else check_inputs()
