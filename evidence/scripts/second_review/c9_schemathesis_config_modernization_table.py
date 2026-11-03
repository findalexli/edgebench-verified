#!/usr/bin/env python3
"""Real agent-16 and its forwarding-wrapper copy on the old and fixed judge (evidence/runs/community9-schemathesis_config_modernization-*)."""
import glob, sys
sys.path.insert(0, "evidence/scripts/second_review")
from c9_common import print_grades
jobs = [p.split("/")[-1] for p in sorted(glob.glob("evidence/runs/community9-schemathesis_config_modernization-[a-z]"))]
print(jobs)
print_grades(jobs, ["starter", "agent16", "agent16_wrapper"])
