#!/usr/bin/env python3
"""Real agent-2, with the hidden names only, and with invalid dates, on the old and fixed judge (evidence/runs/community9-schemathesis_datagen_pipeline-*)."""
import glob, sys
sys.path.insert(0, "evidence/scripts/second_review")
from c9_common import print_grades
jobs = [p.split("/")[-1] for p in sorted(glob.glob("evidence/runs/community9-schemathesis_datagen_pipeline-[a-z]"))]
print(jobs)
print_grades(jobs, ["starter", "agent2", "agent2_named", "agent2_named_sunday", "agent2_named_indep", "agent2_full", "agent2_full_sunday", "agent2_full_indep"])
