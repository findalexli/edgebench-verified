#!/usr/bin/env python3
"""Real agent-12, agent-1 and copies changed at one defect on the old and fixed judge (evidence/runs/community9-schemathesis_reporting_observability-*)."""
import glob, sys
sys.path.insert(0, "evidence/scripts/second_review")
from c9_common import print_grades
jobs = [p.split("/")[-1] for p in sorted(glob.glob("evidence/runs/community9-schemathesis_reporting_observability-[a-z]"))]
print(jobs)
print_grades(jobs, ["starter", "agent12", "agent12_trunc", "agent12_noerr", "agent12_brand", "agent12_nobody", "agent1", "agent1_body"])
