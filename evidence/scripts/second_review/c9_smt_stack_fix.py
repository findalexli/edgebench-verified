#!/usr/bin/env python3
"""Candidate fix for the validator's stack overflow: run validate_sat_witness on a thread with a 1 GiB stack, so a deep witness or benchmark
cannot kill the pool worker and with it the whole evaluation. Applied to the evaluate.py files named on the command line."""
import sys
HELP = '''
def _on_big_stack(fn, *args):
    import threading
    box = {}
    def run():
        try:
            box["value"] = fn(*args)
        except BaseException as exc:
            box["exc"] = exc
    threading.stack_size(1024 * 1024 * 1024)
    t = threading.Thread(target=run)
    t.start()
    t.join()
    if "exc" in box:
        raise box["exc"]
    return box.get("value")


def run_solver_case(args):
'''
for p in sys.argv[1:]:
    s = open(p).read()
    assert s.count('validate_sat_witness(isolated_path, witness)') == 1 and s.count('\ndef run_solver_case(args):\n') == 1
    s = s.replace('validate_sat_witness(isolated_path, witness)', '_on_big_stack(validate_sat_witness, isolated_path, witness)').replace('\ndef run_solver_case(args):\n', HELP)
    open(p, 'w').write(s)
